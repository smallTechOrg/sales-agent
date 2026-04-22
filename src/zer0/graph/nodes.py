"""Graph nodes — one function per node.

Spec: spec/product/10-agent-graph.md — Nodes

Each node accepts AgentState and returns a partial dict merged back into state.
DB writes (stage updates, EventRow inserts, MessageRow inserts) are committed
per-node inside create_db_session() so every action is immediately visible in
the audit trail and UI even if a later node fails.
"""

from __future__ import annotations

import structlog
from datetime import datetime, timezone

from zer0.config.resolver import ConfigResolver
from zer0.db.models import ContactRow, LeadRow, LinkRow, MessageRow
from zer0.db.session import create_db_session
from zer0.domain import Contact, Lead, Link
from zer0.domain.config import ApprovalMode, Channel
from zer0.domain.lead import LeadStage
from zer0.domain.link import LinkSource as LinkSourceModel
from zer0.domain.outreach import SentMessage
from zer0.graph.state import AgentState
from zer0.llm.client import LLMClient
from zer0.observability.events import post_slack_event, write_event
from zer0.tools import (
    check_replies,
    detect_language,
    directory_search,
    draft_outreach,
    duckduckgo_search,
    enrich_lead,
    find_all_contacts,
    identify_leads,
    qualify_lead,
    scrape_page,
    send_email,
    send_whatsapp,
    web_search,
)

log = structlog.get_logger(__name__)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _new_id() -> str:
    import uuid
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# resolve_config
# ---------------------------------------------------------------------------

def node_resolve_config(state: AgentState) -> dict:
    """Resolve campaign config from DB. Aborts run on error."""
    try:
        with create_db_session() as session:
            config = ConfigResolver(session).resolve(
                campaign_id=state["campaign_id"],
                tenant_id=state["tenant_id"],
            )
        return {"config": config}
    except Exception as exc:
        log.error("resolve_config.failed", error=str(exc))
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# discover  →  writes LinkRow rows
# ---------------------------------------------------------------------------

def node_discover(state: AgentState) -> dict:
    """Run discovery tools and persist raw Link rows (URLs only — no scraping yet)."""
    if state.get("error"):
        return {}

    config = state["config"]
    disc = config.discovery_config
    icp = config.icp
    campaign_id = state["campaign_id"]
    tenant_id = state["tenant_id"]

    seen_urls: set[str] = {lnk.url for lnk in state.get("links", [])}

    try:
        with create_db_session() as db_check:
            db_urls = {
                r[0]
                for r in db_check.query(LinkRow.url)
                .filter(LinkRow.tenant_id == tenant_id, LinkRow.campaign_id == campaign_id)
                .all()
            }
        seen_urls.update(db_urls)
    except Exception as exc:
        log.warning("discover.db_dedup_failed", error=str(exc))

    raw_links: list[Link] = []
    settings = None

    base_kwargs: dict = {
        "discovery_config": disc,
        "icp": icp,
        "tenant_id": tenant_id,
        "campaign_id": campaign_id,
    }

    non_web_source_map = {
        "linkedin": (directory_search, LinkSourceModel.linkedin),
        "directory": (directory_search, LinkSourceModel.directory),
    }

    for source_name in [s.value for s in disc.sources]:
        if source_name == "web":
            if settings is None:
                from zer0.config.settings import get_settings
                settings = get_settings()

            web_adapters = [("duckduckgo", duckduckgo_search)]
            if settings.tavily_api_key:
                web_adapters.append(("tavily", web_search))

            for adapter_name, adapter_fn in web_adapters:
                try:
                    kwargs = dict(base_kwargs)
                    if adapter_fn is web_search:
                        kwargs["tavily_api_key"] = settings.tavily_api_key
                    results = adapter_fn(**kwargs)
                    log.info("discover.web_adapter_ok", adapter=adapter_name, count=len(results))
                except Exception as exc:
                    log.warning("discover.tool_failed", source=f"web/{adapter_name}", error=str(exc))
                    results = []

                for r in results:
                    url = getattr(r, "url", None)
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        raw_links.append(Link(
                            id=_new_id(),
                            tenant_id=tenant_id,
                            campaign_id=campaign_id,
                            url=url,
                            source=LinkSourceModel.web,
                        ))

        elif source_name in non_web_source_map:
            tool_fn, lnk_source = non_web_source_map[source_name]
            try:
                results = tool_fn(**base_kwargs)
            except Exception as exc:
                log.warning("discover.tool_failed", source=source_name, error=str(exc))
                results = []

            for r in results:
                url = getattr(r, "url", None)
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    raw_links.append(Link(
                        id=_new_id(),
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        url=url,
                        source=lnk_source,
                    ))

    raw_links = raw_links[: disc.volume_per_run]

    if raw_links:
        try:
            with create_db_session() as session:
                for lnk in raw_links:
                    row = LinkRow(
                        id=lnk.id,
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        url=lnk.url,
                        source=lnk.source.value,
                    )
                    session.add(row)
                    write_event(
                        db=session,
                        event_type="link.discovered",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=None,
                        payload={"url": lnk.url, "source": lnk.source.value},
                    )
        except Exception as exc:
            log.warning("discover.db_write_failed", error=str(exc))

    return {"links": list(state.get("links", [])) + raw_links}


# ---------------------------------------------------------------------------
# scrape_links  →  fills link.page_text
# ---------------------------------------------------------------------------

def node_scrape_links(state: AgentState) -> dict:
    """Scrape each link and store page_text on the Link and in LinkRow."""
    if state.get("error"):
        return {}

    updated: list[Link] = []
    for lnk in state.get("links", []):
        if lnk.page_text:
            updated.append(lnk)
            continue
        try:
            text = scrape_page(url=lnk.url)
            now = _now()
            scraped = lnk.model_copy(update={"page_text": text, "scraped_at": now})
            updated.append(scraped)
            try:
                with create_db_session() as session:
                    row = (
                        session.query(LinkRow)
                        .filter(LinkRow.id == lnk.id, LinkRow.tenant_id == lnk.tenant_id)
                        .first()
                    )
                    if row:
                        row.page_text = text
                        row.scraped_at = now
            except Exception as exc:
                log.warning("scrape_links.db_write_failed", link_id=lnk.id, error=str(exc))
        except Exception as exc:
            log.warning("scrape_links.failed", link_id=lnk.id, url=lnk.url, error=str(exc))
            updated.append(lnk)

    return {"links": updated}


# ---------------------------------------------------------------------------
# identify_leads  →  extracts Lead entities from scraped pages
# ---------------------------------------------------------------------------

def node_identify_leads(state: AgentState) -> dict:
    """Use LLM to identify company entities on each scraped page."""
    if state.get("error"):
        return {}

    config = state["config"]
    llm = LLMClient()
    new_leads: list[Lead] = []
    tenant_id = state["tenant_id"]
    campaign_id = state["campaign_id"]

    for lnk in state.get("links", []):
        if not lnk.page_text:
            continue
        try:
            leads = identify_leads(link=lnk, icp=config.icp, llm=llm, config=config)
            for lead in leads:
                new_leads.append(lead)
                try:
                    with create_db_session() as session:
                        row = LeadRow(
                            id=lead.id,
                            tenant_id=tenant_id,
                            campaign_id=campaign_id,
                            link_id=lnk.id,
                            stage=LeadStage.prospect.value,
                            company_name=lead.company_name,
                            domain=lead.domain,
                            industry=lead.industry,
                            headcount_range=lead.headcount_range,
                            business_type=lead.business_type,
                        )
                        session.add(row)
                        write_event(
                            db=session,
                            event_type="lead.identified",
                            tenant_id=tenant_id,
                            campaign_id=campaign_id,
                            lead_id=lead.id,
                            payload={"company_name": lead.company_name, "link_id": lnk.id},
                        )
                except Exception as exc:
                    log.warning("identify_leads.db_write_failed", lead_id=lead.id, error=str(exc))
        except Exception as exc:
            log.warning("identify_leads.link_failed", link_id=lnk.id, error=str(exc))

    return {"leads": list(state.get("leads", [])) + new_leads}


# ---------------------------------------------------------------------------
# research  →  cumulative enrichment
# ---------------------------------------------------------------------------

def node_research(state: AgentState) -> dict:
    """Enrich leads by appending signals/summary from their source page."""
    if state.get("error"):
        return {}

    config = state["config"]
    llm = LLMClient()
    links_by_id = {lnk.id: lnk for lnk in state.get("links", [])}
    updated_leads: list[Lead] = []

    for lead in state.get("leads", []):
        if lead.stage not in (LeadStage.prospect, LeadStage.research):
            updated_leads.append(lead)
            continue
        try:
            page_text = ""
            if lead.link_id and lead.link_id in links_by_id:
                page_text = links_by_id[lead.link_id].page_text or ""
            elif lead.domain:
                try:
                    page_text = scrape_page(url=f"https://{lead.domain}")
                except Exception:
                    pass

            enriched = enrich_lead(
                lead=lead,
                page_text=page_text,
                icp=config.icp,
                llm=llm,
                config=config,
            )
            updated = enriched.model_copy(update={"stage": LeadStage.research})
            updated_leads.append(updated)

            try:
                with create_db_session() as session:
                    row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead.id, LeadRow.tenant_id == lead.tenant_id)
                        .first()
                    )
                    if row:
                        row.stage = LeadStage.research.value
                        row.research_summary = updated.research_summary
                        row.signals = updated.signals
                        row.last_researched_at = updated.last_researched_at
                    write_event(
                        db=session,
                        event_type="lead.researched",
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        payload={"signals_count": len(updated.signals)},
                    )
            except Exception as exc:
                log.warning("research.db_write_failed", lead_id=lead.id, error=str(exc))

        except Exception as exc:
            log.warning("research.lead_failed", lead_id=lead.id, error=str(exc))
            updated_leads.append(lead)

    return {"leads": updated_leads}


# ---------------------------------------------------------------------------
# qualify
# ---------------------------------------------------------------------------

def node_qualify(state: AgentState) -> dict:
    """Score leads; persist stage, score, and rationale to DB."""
    if state.get("error"):
        return {}

    config = state["config"]
    llm = LLMClient()
    updated_leads: list[Lead] = []

    for lead in state.get("leads", []):
        if lead.stage != LeadStage.research:
            updated_leads.append(lead)
            continue
        try:
            result = qualify_lead(
                lead=lead,
                qualification_config=config.qualification_config,
                llm=llm,
                config=config,
            )
            updated_leads.append(result)

            db_stage = result.stage.value
            event_type = "lead.qualified" if result.stage == LeadStage.qualification else "lead.rejected"

            try:
                with create_db_session() as session:
                    row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead.id, LeadRow.tenant_id == lead.tenant_id)
                        .first()
                    )
                    if row:
                        row.stage = db_stage
                        row.score = result.score
                        row.per_criterion_scores = [s.model_dump() for s in result.per_criterion_scores]
                        row.rationale = result.rationale
                        row.rejection_reason = result.rejection_reason
                    write_event(
                        db=session,
                        event_type=event_type,
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        payload={"stage": db_stage, "score": result.score},
                    )
            except Exception as exc:
                log.warning("qualify.db_write_failed", lead_id=lead.id, error=str(exc))

        except Exception as exc:
            log.warning("qualify.lead_failed", lead_id=lead.id, error=str(exc))
            updated_leads.append(lead)

    return {"leads": updated_leads}


# ---------------------------------------------------------------------------
# get_contacts
# ---------------------------------------------------------------------------

def node_get_contacts(state: AgentState) -> dict:
    """Discover contacts at all qualified leads."""
    if state.get("error"):
        return {}

    config = state["config"]
    new_contacts: list[Contact] = []
    updated_leads: list[Lead] = []

    for lead in state.get("leads", []):
        if lead.stage != LeadStage.qualification:
            updated_leads.append(lead)
            continue
        try:
            contacts = find_all_contacts(
                lead=lead,
                target_roles=config.icp.target_roles,
                config=config,
            )
            for contact in contacts:
                new_contacts.append(contact)
                try:
                    with create_db_session() as session:
                        row = ContactRow(
                            id=contact.id,
                            tenant_id=lead.tenant_id,
                            lead_id=lead.id,
                            first_name=contact.first_name,
                            last_name=contact.last_name,
                            full_name=contact.full_name,
                            email=contact.email,
                            phone=contact.phone,
                            role=contact.role,
                            linkedin_url=contact.linkedin_url,
                        )
                        session.add(row)
                        write_event(
                            db=session,
                            event_type="contact.discovered",
                            tenant_id=lead.tenant_id,
                            campaign_id=lead.campaign_id,
                            lead_id=lead.id,
                            contact_id=contact.id,
                            payload={"role": contact.role},
                        )
                except Exception as exc:
                    log.warning("get_contacts.db_write_failed", contact_id=contact.id, error=str(exc))

            updated_lead = lead.model_copy(update={"stage": LeadStage.contacts})
            updated_leads.append(updated_lead)

            try:
                with create_db_session() as session:
                    row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead.id, LeadRow.tenant_id == lead.tenant_id)
                        .first()
                    )
                    if row:
                        row.stage = LeadStage.contacts.value
                    write_event(
                        db=session,
                        event_type="lead.contacts_found",
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        payload={"count": len(contacts)},
                    )
            except Exception as exc:
                log.warning("get_contacts.lead_stage_failed", lead_id=lead.id, error=str(exc))

        except Exception as exc:
            log.warning("get_contacts.lead_failed", lead_id=lead.id, error=str(exc))
            updated_leads.append(lead)

    return {
        "leads": updated_leads,
        "contacts": list(state.get("contacts", [])) + new_contacts,
    }


# ---------------------------------------------------------------------------
# approval_gate  →  approves contacts for outreach
# ---------------------------------------------------------------------------

def node_approval_gate(state: AgentState) -> dict:
    """Route contacts to outreach or park for human approval.

    Auto modes: contact.approved_for_outreach = True immediately.
    Human modes: park and notify via Slack.
    """
    if state.get("error"):
        return {}

    config = state["config"]
    leads_with_contacts_stage = [l for l in state.get("leads", []) if l.stage == LeadStage.contacts]
    lead_ids = {l.id for l in leads_with_contacts_stage}
    contacts = [c for c in state.get("contacts", []) if c.lead_id in lead_ids]
    tenant_id = state["tenant_id"]
    campaign_id = state["campaign_id"]

    auto_modes = {ApprovalMode.full_auto, ApprovalMode.approve_messages}
    contact_ids = [c.id for c in contacts]

    if config.approval_mode in auto_modes:
        approved_contacts: list[Contact] = []
        if contact_ids:
            try:
                with create_db_session() as session:
                    for contact in contacts:
                        row = (
                            session.query(ContactRow)
                            .filter(ContactRow.id == contact.id, ContactRow.lead_id == contact.lead_id)
                            .first()
                        )
                        if row:
                            row.approved_for_outreach = True
                        write_event(
                            db=session,
                            event_type="approval.granted",
                            tenant_id=tenant_id,
                            campaign_id=campaign_id,
                            lead_id=contact.lead_id,
                            contact_id=contact.id,
                            payload={"auto": True},
                        )
                    # Update lead stage to approval
                    for lead in leads_with_contacts_stage:
                        lead_row = (
                            session.query(LeadRow)
                            .filter(LeadRow.id == lead.id, LeadRow.tenant_id == tenant_id)
                            .first()
                        )
                        if lead_row:
                            lead_row.stage = LeadStage.approval.value
            except Exception as exc:
                log.warning("approval_gate.auto_approve_failed", error=str(exc))
            approved_contacts = [c.model_copy(update={"approved_for_outreach": True}) for c in contacts]

        updated_leads = [
            l.model_copy(update={"stage": LeadStage.approval}) if l.id in lead_ids else l
            for l in state.get("leads", [])
        ]
        all_contacts = [
            c.model_copy(update={"approved_for_outreach": True}) if c.id in {ac.id for ac in approved_contacts} else c
            for c in state.get("contacts", [])
        ]
        return {
            "leads": updated_leads,
            "contacts": all_contacts,
            "approved_contact_ids": contact_ids,
        }

    # Human approval required
    if contact_ids:
        try:
            with create_db_session() as session:
                for contact in contacts:
                    write_event(
                        db=session,
                        event_type="approval.pending",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=contact.lead_id,
                        contact_id=contact.id,
                        payload={},
                    )
        except Exception as exc:
            log.warning("approval_gate.pending_event_failed", error=str(exc))

        if config.slack_webhook_url:
            post_slack_event(
                webhook_url=config.slack_webhook_url,
                event_type="approval.pending",
                tenant_id=tenant_id,
                payload={"pending_count": len(contact_ids), "campaign_id": campaign_id},
            )

    return {"pending_approval_contact_ids": contact_ids, "approved_contact_ids": []}


# ---------------------------------------------------------------------------
# outreach  →  draft and send per approved contact
# ---------------------------------------------------------------------------

def node_outreach(state: AgentState) -> dict:
    """Draft and (optionally) send first-touch messages for each approved contact."""
    if state.get("error"):
        return {}

    config = state["config"]
    llm = LLMClient()
    approved_ids = set(state.get("approved_contact_ids", []))
    leads_map = {l.id: l for l in state.get("leads", [])}
    contacts_map = {c.id: c for c in state.get("contacts", [])}

    drafts = []
    sent = []
    approval_required = config.approval_mode in {ApprovalMode.approve_messages, ApprovalMode.approve_all}
    channels = config.outreach_config.channels_enabled

    for contact_id in approved_ids:
        contact = contacts_map.get(contact_id)
        if not contact:
            continue
        lead = leads_map.get(contact.lead_id)
        if not lead:
            continue

        for channel in channels:
            try:
                lang = detect_language(lead=lead, llm=llm, config=config)
                if lang and not lead.detected_language:
                    lead = lead.model_copy(update={"detected_language": lang})

                msg_draft = draft_outreach(
                    lead=lead,
                    contact=contact,
                    channel=channel,
                    sequence_number=1,
                    llm=llm,
                    config=config,
                )
                drafts.append(msg_draft)

                with create_db_session() as session:
                    lead_row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead.id, LeadRow.tenant_id == lead.tenant_id)
                        .first()
                    )
                    if lead_row and lang:
                        lead_row.detected_language = lang

                    msg_status = "pending_approval" if approval_required else "drafted"
                    msg_row = MessageRow(
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        contact_id=contact.id,
                        channel=channel.value,
                        subject=msg_draft.subject,
                        body=msg_draft.body,
                        personalisation_notes=msg_draft.personalisation_notes,
                        config_snapshot=config.model_dump(),
                        sequence_number=1,
                        status=msg_status,
                    )
                    session.add(msg_row)
                    session.flush()

                    write_event(
                        db=session,
                        event_type="message.drafted",
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        contact_id=contact.id,
                        payload={"channel": channel.value, "sequence": 1, "message_id": msg_row.id},
                    )

                    if approval_required:
                        write_event(
                            db=session,
                            event_type="message.pending_approval",
                            tenant_id=lead.tenant_id,
                            campaign_id=lead.campaign_id,
                            lead_id=lead.id,
                            contact_id=contact.id,
                            payload={"message_id": msg_row.id},
                        )
                        continue

                    sm = _send_message(msg_draft=msg_draft, config=config, lead=lead, contact=contact)
                    sent.append(sm)

                    msg_row.status = "sent"
                    msg_row.sent_at = sm.sent_at
                    msg_row.external_message_id = sm.external_message_id
                    if lead_row:
                        lead_row.stage = LeadStage.outreach.value

                    write_event(
                        db=session,
                        event_type="message.sent",
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        contact_id=contact.id,
                        payload={"channel": channel.value, "sequence": 1},
                    )

            except Exception as exc:
                log.warning(
                    "outreach.contact_failed",
                    contact_id=contact_id,
                    channel=channel.value if hasattr(channel, "value") else str(channel),
                    error=str(exc),
                )

    if approval_required and drafts and config.slack_webhook_url:
        post_slack_event(
            webhook_url=config.slack_webhook_url,
            event_type="message.pending_approval",
            tenant_id=state["tenant_id"],
            payload={"pending_count": len(drafts), "campaign_id": state["campaign_id"]},
        )

    return {
        "outreach_drafts": list(state.get("outreach_drafts", [])) + drafts,
        "sent_messages": list(state.get("sent_messages", [])) + sent,
    }


def _send_message(*, msg_draft, config, lead, contact) -> SentMessage:
    """Call the appropriate send tool and return a SentMessage."""
    from zer0.config.settings import get_settings

    settings = get_settings()
    enc_key = settings.credential_encryption_key.encode()

    if msg_draft.channel == Channel.email:
        return send_email(
            draft=msg_draft,
            encrypted_credentials=(
                config.google_oauth_token_enc.encode() if config.google_oauth_token_enc else b""
            ),
            encryption_key=enc_key,
        )
    else:
        return send_whatsapp(
            draft=msg_draft,
            recipient_phone=contact.phone or "",
            encrypted_credentials=(
                config.whatsapp_api_key_enc.encode() if config.whatsapp_api_key_enc else b""
            ),
            encryption_key=enc_key,
        )


# ---------------------------------------------------------------------------
# check_replies  →  handles positive replies, stops sibling contacts, sends follow-ups
# ---------------------------------------------------------------------------

def node_check_replies(state: AgentState) -> dict:
    """Check replies and send follow-ups for active leads.

    Positive reply from contact A → stop outreach to all sibling contacts,
    set lead.stage = first_contact.
    All follow-ups exhausted with no reply → lead.stage = no_contact.
    """
    if state.get("error"):
        return {}

    config = state["config"]
    now = _now()
    completed = list(state.get("completed_lead_ids", []))
    new_replies = []
    new_sent: list[SentMessage] = []
    tenant_id = state["tenant_id"]
    campaign_id = state["campaign_id"]

    try:
        from zer0.config.settings import get_settings

        settings = get_settings()
        enc_key = settings.credential_encryption_key.encode()
        replies = check_replies(
            campaign_id=campaign_id,
            tenant_id=tenant_id,
            channels=config.outreach_config.channels_enabled,
            encrypted_credentials=(
                config.google_oauth_token_enc.encode() if config.google_oauth_token_enc else b""
            ),
            encryption_key=enc_key,
        )
        new_replies.extend(replies)

        positive_lead_ids = {
            r.lead_id for r in replies if r.sentiment and r.sentiment.value == "positive"
        }
        for lid in positive_lead_ids:
            if lid in completed:
                continue
            completed.append(lid)
            try:
                with create_db_session() as session:
                    # Stop all sibling contacts for this lead
                    session.query(ContactRow).filter(ContactRow.lead_id == lid).update(
                        {"outreach_stopped": True}
                    )
                    lead_row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lid, LeadRow.tenant_id == tenant_id)
                        .first()
                    )
                    if lead_row:
                        lead_row.stage = LeadStage.first_contact.value
                    write_event(
                        db=session,
                        event_type="handoff.triggered",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lid,
                        payload={"reason": "positive_reply"},
                    )
            except Exception as exc:
                log.warning("check_replies.handoff_db_failed", lead_id=lid, error=str(exc))

            if config.slack_webhook_url:
                post_slack_event(
                    webhook_url=config.slack_webhook_url,
                    event_type="handoff.triggered",
                    tenant_id=tenant_id,
                    payload={"lead_id": lid, "campaign_id": campaign_id},
                )

    except Exception as exc:
        log.warning("check_replies.check_failed", error=str(exc))

    # Send follow-ups
    completed_set = set(completed)
    llm = LLMClient()
    leads_map = {l.id: l for l in state.get("leads", [])}
    contacts_map = {c.id: c for c in state.get("contacts", [])}
    max_follow_ups = config.outreach_config.follow_up_count

    last_sent_by_contact: dict[str, SentMessage] = {}
    for m in state.get("sent_messages", []):
        cid = getattr(m, "contact_id", None)
        if cid and (
            cid not in last_sent_by_contact
            or m.sequence_number > last_sent_by_contact[cid].sequence_number
        ):
            last_sent_by_contact[cid] = m

    for contact_id, last_msg in last_sent_by_contact.items():
        contact = contacts_map.get(contact_id)
        if not contact or contact.outreach_stopped:
            continue
        lead_id = contact.lead_id
        if lead_id in completed_set:
            continue
        if last_msg.sent_at is None:
            continue
        elapsed_days = (now - last_msg.sent_at).days
        if elapsed_days < config.outreach_config.follow_up_spacing_days:
            continue

        next_seq = last_msg.sequence_number + 1
        if next_seq > 1 + max_follow_ups:
            completed.append(lead_id)
            completed_set.add(lead_id)
            try:
                with create_db_session() as session:
                    lead_row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead_id, LeadRow.tenant_id == tenant_id)
                        .first()
                    )
                    if lead_row:
                        lead_row.stage = LeadStage.no_contact.value
                    write_event(
                        db=session,
                        event_type="outreach.exhausted",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lead_id,
                        payload={"follow_up_count": max_follow_ups},
                    )
            except Exception as exc:
                log.warning("check_replies.exhausted_db_failed", lead_id=lead_id, error=str(exc))
            continue

        lead = leads_map.get(lead_id)
        if not lead:
            continue

        for channel in config.outreach_config.channels_enabled:
            try:
                fu_draft = draft_outreach(
                    lead=lead,
                    contact=contact,
                    channel=channel,
                    sequence_number=next_seq,
                    llm=llm,
                    config=config,
                )
                sm = _send_message(msg_draft=fu_draft, config=config, lead=lead, contact=contact)
                new_sent.append(sm)

                with create_db_session() as session:
                    msg_row = MessageRow(
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lead.id,
                        contact_id=contact.id,
                        channel=channel.value,
                        body=fu_draft.body,
                        subject=fu_draft.subject,
                        personalisation_notes=fu_draft.personalisation_notes,
                        config_snapshot=config.model_dump(),
                        sequence_number=next_seq,
                        status="sent",
                        sent_at=sm.sent_at,
                        external_message_id=sm.external_message_id,
                    )
                    session.add(msg_row)
                    write_event(
                        db=session,
                        event_type="message.sent",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lead.id,
                        contact_id=contact.id,
                        payload={"channel": channel.value, "sequence": next_seq},
                    )
            except Exception as exc:
                log.warning(
                    "check_replies.send_failed",
                    contact_id=contact_id,
                    channel=channel.value if hasattr(channel, "value") else str(channel),
                    error=str(exc),
                )

    return {
        "replies": list(state.get("replies", [])) + new_replies,
        "sent_messages": list(state.get("sent_messages", [])) + new_sent,
        "completed_lead_ids": completed,
    }


# ---------------------------------------------------------------------------
# handle_error
# ---------------------------------------------------------------------------

def node_handle_error(state: AgentState) -> dict:
    """Write error event to audit log and post Slack alert if configured."""
    err = state.get("error", "unknown error")
    log.error("agent.run_failed", error=err)
    try:
        with create_db_session() as session:
            write_event(
                db=session,
                event_type="run.error",
                tenant_id=state.get("tenant_id", ""),
                campaign_id=state.get("campaign_id"),
                lead_id=None,
                payload={"error": err},
            )
    except Exception as exc:
        log.warning("handle_error.db_write_failed", error=str(exc))

    if state.get("config") and getattr(state["config"], "slack_webhook_url", None):
        post_slack_event(
            webhook_url=state["config"].slack_webhook_url,
            event_type="run.error",
            tenant_id=state.get("tenant_id", ""),
            payload={"error": err},
        )
    return {}

