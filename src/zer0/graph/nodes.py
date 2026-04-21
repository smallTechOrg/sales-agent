"""Graph nodes — one function per node.

Spec: spec/product/05-agent-graph.md — Nodes
Each node accepts AgentState and returns a partial dict merged back into state.
No node reads from the database mid-run; all data flows through state.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog

from zer0.config.resolver import ConfigResolver
from zer0.domain import RawLead
from zer0.domain.config import ApprovalMode, Channel
from zer0.domain.lead import LeadSource
from zer0.graph.state import AgentState
from zer0.llm.client import LLMClient
from zer0.observability.events import post_slack_event, write_event
from zer0.tools import (
    check_replies,
    detect_language,
    directory_search,
    draft_outreach,
    enrich_lead,
    find_contact,
    linkedin_search,
    qualify_lead,
    scrape_page,
    send_email,
    send_whatsapp,
    web_search,
)

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# resolve_config
# ---------------------------------------------------------------------------

def node_resolve_config(state: AgentState) -> dict:
    """Resolve campaign config from DB. Aborts run on error."""
    from zer0.db.session import get_session

    resolver_cls = ConfigResolver
    try:
        session_gen = get_session()
        session = next(session_gen)
        config = resolver_cls(session).resolve(
            campaign_id=state["campaign_id"],
            tenant_id=state["tenant_id"],
        )
        try:
            next(session_gen)
        except StopIteration:
            pass
        return {"config": config}
    except Exception as exc:
        log.error("resolve_config.failed", error=str(exc))
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# discover
# ---------------------------------------------------------------------------

def node_discover(state: AgentState) -> dict:
    """Run discovery tools and return deduplicated raw leads."""
    if state.get("error"):
        return {}

    config = state["config"]
    disc = config.discovery_config
    icp = config.icp
    campaign_id = state["campaign_id"]
    tenant_id = state["tenant_id"]

    seen_urls: set[str] = {l.url for l in state.get("raw_leads", [])}
    raw: list[RawLead] = []

    source_map = {
        "linkedin": (linkedin_search, LeadSource.linkedin),
        "web": (web_search, LeadSource.web),
        "directory": (directory_search, LeadSource.directory),
    }
    settings = None

    for source_name in [s.value for s in disc.sources]:
        entry = source_map.get(source_name)
        if not entry:
            continue
        tool_fn, source_enum = entry
        try:
            kwargs: dict = {
                "discovery_config": disc,
                "icp": icp,
                "tenant_id": tenant_id,
                "campaign_id": campaign_id,
            }
            if tool_fn is web_search:
                if settings is None:
                    from zer0.config.settings import get_settings
                    settings = get_settings()
                kwargs["tavily_api_key"] = settings.tavily_api_key
            results = tool_fn(**kwargs)
        except Exception as exc:
            log.warning("discover.tool_failed", source=source_name, error=str(exc))
            results = []

        for r in results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                raw.append(r)

    cap = disc.volume_per_run
    raw = raw[:cap]

    for lead in raw:
        write_event(
            db=None,
            event_type="lead.discovered",
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            lead_id=lead.id,
            payload={"url": lead.url, "source": lead.source},
        )

    return {"raw_leads": list(state.get("raw_leads", [])) + raw}


# ---------------------------------------------------------------------------
# research
# ---------------------------------------------------------------------------

def node_research(state: AgentState) -> dict:
    if state.get("error"):
        return {}

    config = state["config"]
    llm = LLMClient()
    enriched = []

    for lead in state.get("raw_leads", []):
        try:
            page_text = scrape_page(url=lead.url)
            contact = find_contact(url=lead.url, target_roles=config.icp.target_roles)
            el = enrich_lead(
                raw_lead=lead,
                icp=config.icp,
                page_text=page_text,
                contact_name=contact.name if contact else None,
                contact_email=contact.email if contact else None,
                contact_phone=contact.phone if contact else None,
                contact_role=contact.role if contact else None,
                llm=llm,
                config=config,
            )
            enriched.append(el)
            write_event(
                db=None,
                event_type="lead.enriched",
                tenant_id=lead.tenant_id,
                campaign_id=lead.campaign_id,
                lead_id=lead.id,
                payload={},
            )
        except Exception as exc:
            log.warning("research.lead_failed", lead_id=lead.id, error=str(exc))

    return {"enriched_leads": enriched}


# ---------------------------------------------------------------------------
# qualify
# ---------------------------------------------------------------------------

def node_qualify(state: AgentState) -> dict:
    if state.get("error"):
        return {}

    config = state["config"]
    llm = LLMClient()
    qualified = []
    rejected = []

    for lead in state.get("enriched_leads", []):
        try:
            result = qualify_lead(
                lead=lead,
                qualification_config=config.qualification_config,
                llm=llm,
                config=config,
            )
            from zer0.domain import QualifiedLead, RejectedLead
            if isinstance(result, QualifiedLead):
                qualified.append(result)
                event_type = "lead.qualified"
            else:
                rejected.append(result)
                event_type = "lead.rejected"

            write_event(
                db=None,
                event_type=event_type,
                tenant_id=lead.tenant_id,
                campaign_id=lead.campaign_id,
                lead_id=lead.id,
                payload={},
            )
        except Exception as exc:
            log.warning("qualify.lead_failed", lead_id=lead.id, error=str(exc))

    return {"qualified_leads": qualified, "rejected_leads": rejected}


# ---------------------------------------------------------------------------
# approval_gate
# ---------------------------------------------------------------------------

def node_approval_gate(state: AgentState) -> dict:
    if state.get("error"):
        return {}

    config = state["config"]
    qualified = state.get("qualified_leads", [])

    auto_modes = {ApprovalMode.full_auto, ApprovalMode.approve_messages}
    if config.approval_mode in auto_modes:
        return {"approved_lead_ids": [l.id for l in qualified]}

    # Human approval required — park and notify
    pending_ids = [l.id for l in qualified]
    for lead in qualified:
        write_event(
            db=None,
            event_type="approval.pending",
            tenant_id=lead.tenant_id,
            campaign_id=lead.campaign_id,
            lead_id=lead.id,
            payload={"score": lead.score},
        )
    if config.slack_webhook_url and pending_ids:
        post_slack_event(
            webhook_url=config.slack_webhook_url,
            event_type="approval.pending",
            tenant_id=state["tenant_id"],
            payload={"pending_count": len(pending_ids), "campaign_id": state["campaign_id"]},
        )

    return {"pending_approval_lead_ids": pending_ids, "approved_lead_ids": []}


# ---------------------------------------------------------------------------
# outreach
# ---------------------------------------------------------------------------

def node_outreach(state: AgentState) -> dict:
    if state.get("error"):
        return {}

    config = state["config"]
    llm = LLMClient()
    approved_ids = set(state.get("approved_lead_ids", []))
    qualified_map = {l.id: l for l in state.get("qualified_leads", [])}

    drafts = []
    sent = []
    pending_approval_msg_ids = []

    channels = config.outreach_config.channels_enabled

    for lead_id in approved_ids:
        lead = qualified_map.get(lead_id)
        if not lead:
            continue

        for channel in channels:
            try:
                lang_lead = state.get("enriched_leads", [])
                enriched_map = {e.id: e for e in lang_lead}
                enriched = enriched_map.get(lead_id)
                if enriched:
                    lang = detect_language(lead=enriched, llm=llm, config=config)
                    enriched.detected_language = lang

                msg_draft = draft_outreach(
                    lead=lead,
                    channel=channel,
                    sequence_number=1,
                    llm=llm,
                    config=config,
                )
                drafts.append(msg_draft)

                approval_required = config.approval_mode in {ApprovalMode.approve_messages, ApprovalMode.approve_all}
                if approval_required:
                    pending_approval_msg_ids.append(lead_id)
                    write_event(
                        db=None,
                        event_type="message.pending_approval",
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        payload={"channel": channel.value},
                    )
                    continue

                # Auto-send
                _send(msg_draft=msg_draft, config=config, sent=sent, lead=lead)

            except Exception as exc:
                log.warning("outreach.lead_failed", lead_id=lead_id, error=str(exc))

    return {
        "outreach_drafts": list(state.get("outreach_drafts", [])) + drafts,
        "sent_messages": list(state.get("sent_messages", [])) + sent,
    }


def _send(*, msg_draft, config, sent, lead) -> None:
    from zer0.config.settings import get_settings
    settings = get_settings()
    enc_key = settings.credential_encryption_key.encode()

    if msg_draft.channel == Channel.email:
        sm = send_email(
            draft=msg_draft,
            encrypted_credentials=config.google_oauth_token_enc.encode(),
            encryption_key=enc_key,
        )
    else:
        sm = send_whatsapp(
            draft=msg_draft,
            recipient_phone=lead.contact_phone or "",
            encrypted_credentials=config.whatsapp_api_key_enc.encode(),
            encryption_key=enc_key,
        )
    sent.append(sm)
    write_event(
        db=None,
        event_type="message.sent",
        tenant_id=lead.tenant_id,
        campaign_id=lead.campaign_id,
        lead_id=lead.id,
        payload={"channel": msg_draft.channel.value},
    )


# ---------------------------------------------------------------------------
# follow_up_loop
# ---------------------------------------------------------------------------

def node_follow_up_loop(state: AgentState) -> dict:
    if state.get("error"):
        return {}

    config = state["config"]
    now = datetime.now(tz=timezone.utc)
    completed = list(state.get("completed_lead_ids", []))
    new_replies = []
    new_sent = []

    # Check replies (best-effort; credentials may not be available here)
    try:
        from zer0.config.settings import get_settings
        settings = get_settings()
        enc_key = settings.credential_encryption_key.encode()
        replies = check_replies(
            campaign_id=state["campaign_id"],
            tenant_id=state["tenant_id"],
            channels=config.outreach_config.channels_enabled,
            encrypted_credentials=(
                config.google_oauth_token_enc.encode()
                if config.google_oauth_token_enc
                else b""
            ),
            encryption_key=enc_key,
        )
        new_replies.extend(replies)

        positive_lead_ids = {r.lead_id for r in replies if r.sentiment and r.sentiment.value == "positive"}
        for lid in positive_lead_ids:
            if lid not in completed:
                completed.append(lid)
                write_event(
                    db=None,
                    event_type="handoff.triggered",
                    tenant_id=state["tenant_id"],
                    campaign_id=state["campaign_id"],
                    lead_id=lid,
                    payload={},
                )
    except Exception as exc:
        log.warning("follow_up_loop.check_replies_failed", error=str(exc))

    return {
        "replies": list(state.get("replies", [])) + new_replies,
        "sent_messages": list(state.get("sent_messages", [])) + new_sent,
        "completed_lead_ids": completed,
    }


# ---------------------------------------------------------------------------
# handle_error
# ---------------------------------------------------------------------------

def node_handle_error(state: AgentState) -> dict:
    err = state.get("error", "unknown error")
    log.error("agent.run_failed", error=err)
    write_event(
        db=None,
        event_type="run.error",
        tenant_id=state.get("tenant_id", ""),
        campaign_id=state.get("campaign_id"),
        lead_id=None,
        payload={"error": err},
    )
    if state.get("config") and getattr(state["config"], "slack_webhook_url", None):
        post_slack_event(
            webhook_url=state["config"].slack_webhook_url,
            event_type="run.error",
            tenant_id=state.get("tenant_id", ""),
            payload={"error": err},
        )
    return {}
