"""Graph nodes — one function per node.

Spec: spec/product/10-agent-graph.md — Nodes

Each node accepts AgentState and returns a partial dict merged back into state.
DB writes (LeadRow stage updates, EventRow inserts, MessageRow inserts) are
committed per-node inside create_db_session() so every action is immediately
visible in the audit trail and UI even if a later node fails.
"""

from __future__ import annotations

import structlog
from datetime import datetime, timezone

from zer0.config.resolver import ConfigResolver
from zer0.db.models import LeadRow, MessageRow
from zer0.db.session import create_db_session
from zer0.domain import QualifiedLead, RawLead, RejectedLead
from zer0.domain.config import ApprovalMode, Channel
from zer0.domain.lead import LeadSource
from zer0.domain.outreach import SentMessage
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


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


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
# discover
# ---------------------------------------------------------------------------

def node_discover(state: AgentState) -> dict:
    """Run discovery tools, deduplicate, persist LeadRow rows and events."""
    if state.get("error"):
        return {}

    config = state["config"]
    disc = config.discovery_config
    icp = config.icp
    campaign_id = state["campaign_id"]
    tenant_id = state["tenant_id"]

    # Dedup against URLs already in state for this invocation
    seen_urls: set[str] = {lead.url for lead in state.get("raw_leads", [])}

    # Also dedup against already-persisted leads for this campaign (re-run safety)
    try:
        with create_db_session() as db_check:
            db_urls = {
                r[0]
                for r in db_check.query(LeadRow.url)
                .filter(LeadRow.tenant_id == tenant_id, LeadRow.campaign_id == campaign_id)
                .all()
            }
        seen_urls.update(db_urls)
    except Exception as exc:
        log.warning("discover.db_dedup_failed", error=str(exc))

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
        tool_fn, _ = entry
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

    raw = raw[: disc.volume_per_run]

    # Persist new LeadRow rows and lead.discovered events — one session per node
    if raw:
        try:
            with create_db_session() as session:
                for lead in raw:
                    row = LeadRow(
                        id=lead.id,
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        stage="discovered",
                        name=lead.name,
                        company=lead.company,
                        url=lead.url,
                        source=lead.source.value,
                        discovered_at=_now(),
                    )
                    session.add(row)
                    write_event(
                        db=session,
                        event_type="lead.discovered",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lead.id,
                        payload={"url": lead.url, "source": lead.source.value},
                    )
        except Exception as exc:
            log.warning("discover.db_write_failed", error=str(exc))

    return {"raw_leads": list(state.get("raw_leads", [])) + raw}


# ---------------------------------------------------------------------------
# research
# ---------------------------------------------------------------------------

def node_research(state: AgentState) -> dict:
    """Enrich raw leads; persist stage='enriched' and enriched_data to DB."""
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

            enriched_data = {
                "company_summary": el.company_summary,
                "role_summary": el.role_summary,
                "recent_signals": el.recent_signals,
                "contact_email": el.contact_email,
                "contact_phone": el.contact_phone,
                "contact_role": el.contact_role,
            }
            try:
                with create_db_session() as session:
                    row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead.id, LeadRow.tenant_id == lead.tenant_id)
                        .first()
                    )
                    if row:
                        row.stage = "enriched"
                        row.enriched_data = enriched_data
                    write_event(
                        db=session,
                        event_type="lead.enriched",
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        payload={},
                    )
            except Exception as exc:
                log.warning("research.db_write_failed", lead_id=lead.id, error=str(exc))

        except Exception as exc:
            log.warning("research.lead_failed", lead_id=lead.id, error=str(exc))

    return {"enriched_leads": enriched}


# ---------------------------------------------------------------------------
# qualify
# ---------------------------------------------------------------------------

def node_qualify(state: AgentState) -> dict:
    """Score leads; persist stage, score, and rationale to DB."""
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
            if isinstance(result, QualifiedLead):
                qualified.append(result)
                event_type = "lead.qualified"
                db_updates = {
                    "stage": "qualified",
                    "score": result.score,
                    "per_criterion_scores": [s.model_dump() for s in result.per_criterion_scores],
                    "rationale": result.rationale,
                }
            else:
                rejected.append(result)
                event_type = "lead.rejected"
                db_updates = {
                    "stage": "rejected",
                    "score": None,
                    "per_criterion_scores": [s.model_dump() for s in result.per_criterion_scores],
                    "rejection_reason": result.rejection_reason,
                }

            try:
                with create_db_session() as session:
                    row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead.id, LeadRow.tenant_id == lead.tenant_id)
                        .first()
                    )
                    if row:
                        for field, value in db_updates.items():
                            setattr(row, field, value)
                    write_event(
                        db=session,
                        event_type=event_type,
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        payload={"stage": db_updates["stage"]},
                    )
            except Exception as exc:
                log.warning("qualify.db_write_failed", lead_id=lead.id, error=str(exc))

        except Exception as exc:
            log.warning("qualify.lead_failed", lead_id=lead.id, error=str(exc))

    return {"qualified_leads": qualified, "rejected_leads": rejected}


# ---------------------------------------------------------------------------
# approval_gate
# ---------------------------------------------------------------------------

def node_approval_gate(state: AgentState) -> dict:
    """Route leads to outreach or park for human approval.

    Auto modes (full_auto, approve_messages): stage → 'approved' immediately.
    Human modes (approve_qualify, approve_all): stage stays 'qualified', parks run.
    Writes approval events and posts Slack notification.
    """
    if state.get("error"):
        return {}

    config = state["config"]
    qualified = state.get("qualified_leads", [])
    tenant_id = state["tenant_id"]
    campaign_id = state["campaign_id"]

    auto_modes = {ApprovalMode.full_auto, ApprovalMode.approve_messages}

    approved_ids = [l.id for l in qualified]

    if config.approval_mode in auto_modes:
        # Auto-approve — set lead stage to 'approved'
        if approved_ids:
            try:
                with create_db_session() as session:
                    for lead in qualified:
                        row = (
                            session.query(LeadRow)
                            .filter(LeadRow.id == lead.id, LeadRow.tenant_id == tenant_id)
                            .first()
                        )
                        if row:
                            row.stage = "approved"
                        write_event(
                            db=session,
                            event_type="approval.granted",
                            tenant_id=tenant_id,
                            campaign_id=campaign_id,
                            lead_id=lead.id,
                            payload={"auto": True, "score": lead.score},
                        )
            except Exception as exc:
                log.warning("approval_gate.auto_approve_failed", error=str(exc))
        return {"approved_lead_ids": approved_ids}

    # Human approval required — park and notify
    pending_ids = approved_ids  # same list, stage stays 'qualified'
    if pending_ids:
        try:
            with create_db_session() as session:
                for lead in qualified:
                    write_event(
                        db=session,
                        event_type="approval.pending",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lead.id,
                        payload={"score": lead.score},
                    )
        except Exception as exc:
            log.warning("approval_gate.pending_event_failed", error=str(exc))

        if config.slack_webhook_url:
            post_slack_event(
                webhook_url=config.slack_webhook_url,
                event_type="approval.pending",
                tenant_id=tenant_id,
                payload={"pending_count": len(pending_ids), "campaign_id": campaign_id},
            )

    return {"pending_approval_lead_ids": pending_ids, "approved_lead_ids": []}


# ---------------------------------------------------------------------------
# outreach
# ---------------------------------------------------------------------------

def node_outreach(state: AgentState) -> dict:
    """Draft and (optionally) send first-touch messages for each approved lead.

    Creates a MessageRow for every draft. Status is 'pending_approval' when
    operator review is required, otherwise the message is sent immediately and
    the row is updated to 'sent'. Lead stage is set to 'outreach_active' on send.
    """
    if state.get("error"):
        return {}

    config = state["config"]
    llm = LLMClient()
    approved_ids = set(state.get("approved_lead_ids", []))
    qualified_map = {l.id: l for l in state.get("qualified_leads", [])}
    enriched_map = {e.id: e for e in state.get("enriched_leads", [])}

    drafts = []
    sent = []
    approval_required = config.approval_mode in {ApprovalMode.approve_messages, ApprovalMode.approve_all}
    channels = config.outreach_config.channels_enabled

    for lead_id in approved_ids:
        lead = qualified_map.get(lead_id)
        if not lead:
            continue

        for channel in channels:
            try:
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

                with create_db_session() as session:
                    # Persist detected language
                    lead_row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead_id, LeadRow.tenant_id == lead.tenant_id)
                        .first()
                    )
                    if lead_row and enriched and enriched.detected_language:
                        lead_row.detected_language = enriched.detected_language

                    msg_status = "pending_approval" if approval_required else "drafted"
                    msg_row = MessageRow(
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        channel=channel.value,
                        subject=msg_draft.subject,
                        body=msg_draft.body,
                        personalisation_notes=msg_draft.personalisation_notes,
                        config_snapshot=config.model_dump(),
                        sequence_number=1,
                        status=msg_status,
                    )
                    session.add(msg_row)
                    session.flush()  # assign row ID before writing events

                    write_event(
                        db=session,
                        event_type="message.drafted",
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        payload={"channel": channel.value, "sequence": 1, "message_id": msg_row.id},
                    )

                    if approval_required:
                        write_event(
                            db=session,
                            event_type="message.pending_approval",
                            tenant_id=lead.tenant_id,
                            campaign_id=lead.campaign_id,
                            lead_id=lead.id,
                            payload={"message_id": msg_row.id},
                        )
                        continue  # session commits on 'with' exit; go to next channel

                    # Auto-send
                    sm = _send_message(msg_draft=msg_draft, config=config, lead=lead)
                    sent.append(sm)

                    msg_row.status = "sent"
                    msg_row.sent_at = sm.sent_at
                    msg_row.external_message_id = sm.external_message_id
                    if lead_row:
                        lead_row.stage = "outreach_active"

                    write_event(
                        db=session,
                        event_type="message.sent",
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        payload={"channel": channel.value, "sequence": 1},
                    )

            except Exception as exc:
                log.warning(
                    "outreach.lead_failed",
                    lead_id=lead_id,
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


def _send_message(*, msg_draft, config, lead) -> SentMessage:
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
            recipient_phone=lead.contact_phone or "",
            encrypted_credentials=(
                config.whatsapp_api_key_enc.encode() if config.whatsapp_api_key_enc else b""
            ),
            encryption_key=enc_key,
        )


# ---------------------------------------------------------------------------
# follow_up_loop
# ---------------------------------------------------------------------------

def node_follow_up_loop(state: AgentState) -> dict:
    """Check replies and send next follow-ups for active leads.

    Spec: spec/product/10-agent-graph.md — follow_up_loop node
    - Positive reply → write handoff events, post Slack, stage='responded'
    - Spacing elapsed + follow-ups remaining → draft and send follow-up
    - All follow-ups exhausted with no reply → stage='responded', mark completed
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

    # --- Check for inbound replies ---
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
                    lead_row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lid, LeadRow.tenant_id == tenant_id)
                        .first()
                    )
                    if lead_row:
                        lead_row.stage = "responded"
                    write_event(
                        db=session,
                        event_type="handoff.triggered",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lid,
                        payload={"reason": "positive_reply"},
                    )
            except Exception as exc:
                log.warning("follow_up_loop.handoff_db_failed", lead_id=lid, error=str(exc))

            if config.slack_webhook_url:
                post_slack_event(
                    webhook_url=config.slack_webhook_url,
                    event_type="handoff.triggered",
                    tenant_id=tenant_id,
                    payload={"lead_id": lid, "campaign_id": campaign_id},
                )

    except Exception as exc:
        log.warning("follow_up_loop.check_replies_failed", error=str(exc))

    # --- Send follow-ups ---
    completed_set = set(completed)
    llm = LLMClient()
    qualified_map = {l.id: l for l in state.get("qualified_leads", [])}
    max_follow_ups = config.outreach_config.follow_up_count  # follow-up messages after first touch

    # Build map of lead_id → most recent SentMessage
    last_sent_by_lead: dict[str, SentMessage] = {}
    for m in state.get("sent_messages", []):
        if (
            m.lead_id not in last_sent_by_lead
            or m.sequence_number > last_sent_by_lead[m.lead_id].sequence_number
        ):
            last_sent_by_lead[m.lead_id] = m

    for lead_id, last_msg in last_sent_by_lead.items():
        if lead_id in completed_set:
            continue
        if last_msg.sent_at is None:
            continue
        elapsed_days = (now - last_msg.sent_at).days
        if elapsed_days < config.outreach_config.follow_up_spacing_days:
            continue

        next_seq = last_msg.sequence_number + 1
        if next_seq > 1 + max_follow_ups:  # 1 = first touch; 1+N ≥ exhausted
            # All follow-ups exhausted — mark responded
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
                        lead_row.stage = "responded"
                    write_event(
                        db=session,
                        event_type="outreach.exhausted",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lead_id,
                        payload={"follow_up_count": max_follow_ups},
                    )
            except Exception as exc:
                log.warning("follow_up_loop.exhausted_db_failed", lead_id=lead_id, error=str(exc))
            continue

        lead = qualified_map.get(lead_id)
        if not lead:
            continue

        for channel in config.outreach_config.channels_enabled:
            try:
                fu_draft = draft_outreach(
                    lead=lead,
                    channel=channel,
                    sequence_number=next_seq,
                    llm=llm,
                    config=config,
                )
                sm = _send_message(msg_draft=fu_draft, config=config, lead=lead)
                new_sent.append(sm)

                with create_db_session() as session:
                    msg_row = MessageRow(
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lead.id,
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
                        payload={"channel": channel.value, "sequence": next_seq},
                    )
            except Exception as exc:
                log.warning(
                    "follow_up_loop.send_failed",
                    lead_id=lead_id,
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


