"""Approvals endpoints.

Spec: spec/product/09-api.md — /approvals
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from zer0.api._common import api_error, get_current_tenant_id, ok, paginated
from zer0.db import LeadRow, MessageRow, get_session
from zer0.db.models import ContactRow
from zer0.observability.events import write_event

router = APIRouter(prefix="/approvals")


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str | None = None  # optional rejection reason
    body: str | None = None    # optional message body edit (approve-message only)


@router.get("")
def list_pending_approvals(
    campaign_id: str | None = None,
    type: str | None = None,  # "qualify" | "message"
    cursor: str | None = None,
    limit: int = 50,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """List leads and messages currently pending approval.

    Spec: spec/product/09-api.md — GET /approvals
    """
    items = []

    if type in (None, "qualify"):
        leads_q = session.query(LeadRow).filter(
            LeadRow.tenant_id == tenant_id,
            LeadRow.stage == "approval",  # LeadStage.approval — awaiting human review
        )
        if campaign_id:
            leads_q = leads_q.filter(LeadRow.campaign_id == campaign_id)
        if cursor:
            leads_q = leads_q.filter(LeadRow.id > cursor)
        pending_leads = leads_q.order_by(LeadRow.id).limit(limit).all()
        items += [
            {
                "type": "lead",
                "id": lead.id,
                "campaign_id": lead.campaign_id,
                "stage": lead.stage,
                "score": float(lead.score) if lead.score is not None else None,
                "name": lead.company_name,
                "company": lead.company_name,
                "url": lead.domain,
                "rationale": lead.rationale,
            }
            for lead in pending_leads
        ]

    if type in (None, "message"):
        msgs_q = session.query(MessageRow).filter(
            MessageRow.tenant_id == tenant_id,
            MessageRow.status == "pending_approval",
        )
        if campaign_id:
            msgs_q = msgs_q.filter(MessageRow.campaign_id == campaign_id)
        if cursor:
            msgs_q = msgs_q.filter(MessageRow.id > cursor)
        pending_msgs = msgs_q.order_by(MessageRow.id).limit(limit).all()
        items += [
            {
                "type": "message",
                "id": msg.id,
                "lead_id": msg.lead_id,
                "channel": msg.channel,
                "subject": msg.subject,
                "body": msg.body,
                "sequence_number": msg.sequence_number,
                "personalisation_notes": msg.personalisation_notes,
            }
            for msg in pending_msgs
        ]

    next_cursor = items[-1]["id"] if len(items) == limit else None
    return paginated(items, next_cursor)


@router.post("/leads/{lead_id}/qualify")
def qualify_approval(
    lead_id: str,
    body: ApprovalDecision,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """Approve or reject a qualified lead awaiting human review.

    Spec: spec/product/09-api.md — POST /approvals/leads/{lead_id}/qualify
    """
    row: LeadRow | None = (
        session.query(LeadRow)
        .filter(LeadRow.id == lead_id, LeadRow.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise api_error("NOT_FOUND", "Lead not found", 404)

    if body.decision == "approve":
        # Move lead to outreach stage so the next run picks it up.
        # Spec: spec/product/04-capabilities/08-approval.md — approve → outreach
        row.stage = "outreach"
        # Mark all contacts for this lead as approved for outreach.
        session.query(ContactRow).filter(
            ContactRow.lead_id == lead_id,
            ContactRow.tenant_id == tenant_id,
        ).update({"approved_for_outreach": True})
        event_type = "approval.granted"
    else:
        row.stage = "rejected"
        if body.reason:
            row.rejection_reason = body.reason
        event_type = "approval.rejected"

    session.add(row)
    write_event(
        db=session,
        event_type=event_type,
        tenant_id=tenant_id,
        campaign_id=row.campaign_id,
        lead_id=lead_id,
        payload={"decision": body.decision, "reason": body.reason},
    )
    return ok({"decision": body.decision})


@router.post("/messages/{message_id}")
def message_approval(
    message_id: str,
    body: ApprovalDecision,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """Approve or reject a message draft; send immediately on approval.

    Spec: spec/product/09-api.md — POST /approvals/messages/{message_id}
    Operator may optionally edit the message body when approving.
    """
    row: MessageRow | None = (
        session.query(MessageRow)
        .filter(MessageRow.id == message_id, MessageRow.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise api_error("NOT_FOUND", "Message not found", 404)

    if body.decision == "reject":
        row.status = "rejected"
        session.add(row)
        write_event(
            db=session,
            event_type="message.rejected",
            tenant_id=tenant_id,
            campaign_id=row.campaign_id,
            lead_id=row.lead_id,
            payload={"message_id": message_id},
        )
        return ok({"decision": "reject"})

    # Approve — optionally edit body, then send
    if body.body is not None:
        row.body = body.body

    try:
        from zer0.domain.config import Channel, ResolvedConfig
        from zer0.graph.nodes import _send_message
        from zer0.domain.outreach import OutreachDraft

        config = ResolvedConfig.model_validate(row.config_snapshot) if row.config_snapshot else None

        if config:
            # Reconstruct minimal OutreachDraft from the MessageRow
            mock_draft = OutreachDraft(
                lead_id=row.lead_id,
                campaign_id=row.campaign_id,
                tenant_id=tenant_id,
                channel=Channel(row.channel),
                subject=row.subject,
                body=row.body,
                personalisation_notes=row.personalisation_notes or "",
                config_snapshot=config,
                sequence_number=row.sequence_number,
            )

            # Get lead contact info for WhatsApp send
            lead_row = session.query(LeadRow).filter(
                LeadRow.id == row.lead_id, LeadRow.tenant_id == tenant_id
            ).first()

            # Build a minimal lead object for _send_message
            class _LeadProxy:
                contact_phone = (lead_row.enriched_data or {}).get("contact_phone", "") if lead_row else ""

            sm = _send_message(msg_draft=mock_draft, config=config, lead=_LeadProxy())

            row.status = "sent"
            row.sent_at = sm.sent_at
            row.external_message_id = sm.external_message_id
        else:
            row.status = "approved"  # no config snapshot — mark approved but cannot send
    except Exception as exc:
        import structlog
        structlog.get_logger(__name__).warning(
            "message_approval.send_failed", message_id=message_id, error=str(exc)
        )
        row.status = "approved"  # safe fallback — visible in UI for manual action

    session.add(row)
    write_event(
        db=session,
        event_type="message.sent" if row.status == "sent" else "message.approved",
        tenant_id=tenant_id,
        campaign_id=row.campaign_id,
        lead_id=row.lead_id,
        payload={"message_id": message_id, "status": row.status},
    )
    return ok({"decision": "approve"})
