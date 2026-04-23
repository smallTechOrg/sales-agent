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
from zer0.db.models import PersonRow
from zer0.observability.events import write_event

router = APIRouter(prefix="/approvals")


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str | None = None  # optional rejection reason
    body: str | None = None    # optional message body edit (approve-message only)
    approved_person_ids: list[str] | None = None


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
        people = session.query(PersonRow).filter(
            PersonRow.lead_id == lead_id,
            PersonRow.tenant_id == tenant_id,
        ).all()
        selected_person_ids = set(body.approved_person_ids or [person.id for person in people])
        if people and not selected_person_ids:
            raise api_error("INVALID_REQUEST", "approved_person_ids must not be empty when approving", 400)
        for person in people:
            person.approved_for_outreach = person.id in selected_person_ids
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
        payload={
            "decision": body.decision,
            "reason": body.reason,
            "approved_person_ids": body.approved_person_ids,
        },
    )
    return ok({
        "lead_id": lead_id,
        "decision": body.decision,
        "approved_person_ids": body.approved_person_ids,
    })


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

            person_row = None
            if row.person_id:
                person_row = session.query(PersonRow).filter(
                    PersonRow.id == row.person_id,
                    PersonRow.tenant_id == tenant_id,
                ).first()

            class _LeadProxy:
                pass

            class _PersonProxy:
                phone = person_row.phone if person_row else ""

            sm = _send_message(
                msg_draft=mock_draft,
                config=config,
                lead=_LeadProxy(),
                person=_PersonProxy(),
            )

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
