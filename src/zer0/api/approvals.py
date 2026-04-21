"""Approvals endpoints.

Spec: spec/product/04-api.md — /approvals
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from zer0.api._common import api_error, get_current_tenant_id, ok, paginated
from zer0.db import LeadRow, MessageRow, get_session

router = APIRouter(prefix="/approvals")


class ApprovalDecision(BaseModel):
    approved: bool
    note: str | None = None


@router.get("")
def list_pending_approvals(
    cursor: str | None = None,
    limit: int = 50,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """List leads and messages currently pending approval."""
    leads_q = (
        session.query(LeadRow)
        .filter(LeadRow.tenant_id == tenant_id, LeadRow.stage == "qualified")
    )
    msgs_q = (
        session.query(MessageRow)
        .filter(MessageRow.tenant_id == tenant_id, MessageRow.status == "pending_approval")
    )
    if cursor:
        leads_q = leads_q.filter(LeadRow.id > cursor)
        msgs_q = msgs_q.filter(MessageRow.id > cursor)

    pending_leads = leads_q.order_by(LeadRow.id).limit(limit).all()
    pending_msgs = msgs_q.order_by(MessageRow.id).limit(limit).all()

    items = (
        [{"type": "lead", "id": l.id, "campaign_id": l.campaign_id} for l in pending_leads]
        + [{"type": "message", "id": m.id, "lead_id": m.lead_id} for m in pending_msgs]
    )
    return paginated(items, None)


@router.post("/leads/{lead_id}/qualify")
def qualify_approval(
    lead_id: str,
    body: ApprovalDecision,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """Approve or reject a qualified lead awaiting human review."""
    row: LeadRow | None = (
        session.query(LeadRow)
        .filter(LeadRow.id == lead_id, LeadRow.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise api_error("NOT_FOUND", "Lead not found", 404)

    row.stage = "approved" if body.approved else "rejected"
    if not body.approved and body.note:
        row.rejection_reason = body.note
    session.add(row)
    return ok({"lead_id": lead_id, "approved": body.approved})


@router.post("/messages/{message_id}")
def message_approval(
    message_id: str,
    body: ApprovalDecision,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """Approve or reject a message draft awaiting human review."""
    row: MessageRow | None = (
        session.query(MessageRow)
        .filter(MessageRow.id == message_id, MessageRow.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise api_error("NOT_FOUND", "Message not found", 404)

    row.status = "approved" if body.approved else "rejected"
    session.add(row)
    return ok({"message_id": message_id, "approved": body.approved})
