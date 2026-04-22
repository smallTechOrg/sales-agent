"""Messages endpoints.

Spec: spec/product/04-api.md — /messages
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from zer0.api._common import get_current_tenant_id, ok, paginated
from zer0.db import MessageRow, get_session

router = APIRouter(prefix="/messages")


class MessageOut(BaseModel):
    id: str
    tenant_id: str
    campaign_id: str
    lead_id: str
    channel: str
    subject: str | None
    body: str
    sequence_number: int
    status: str
    sent_at: datetime | None
    external_message_id: str | None
    created_at: datetime


def _row_to_out(m: MessageRow) -> MessageOut:
    return MessageOut(
        id=m.id, tenant_id=m.tenant_id, campaign_id=m.campaign_id, lead_id=m.lead_id,
        channel=m.channel, subject=m.subject, body=m.body,
        sequence_number=m.sequence_number, status=m.status,
        sent_at=m.sent_at, external_message_id=m.external_message_id,
        created_at=m.created_at,
    )


@router.get("")
def list_messages(
    campaign_id: str | None = None,
    lead_id: str | None = None,
    cursor: str | None = None,
    limit: int = 50,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    q = session.query(MessageRow).filter(MessageRow.tenant_id == tenant_id)
    if campaign_id:
        q = q.filter(MessageRow.campaign_id == campaign_id)
    if lead_id:
        q = q.filter(MessageRow.lead_id == lead_id)
    if cursor:
        q = q.filter(MessageRow.id > cursor)
    rows = q.order_by(MessageRow.id).limit(limit + 1).all()
    next_cur = rows[-1].id if len(rows) > limit else None
    return paginated([_row_to_out(r) for r in rows[:limit]], next_cur)


@router.get("/{message_id}")
def get_message(
    message_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    from zer0.api._common import api_error
    row = session.query(MessageRow).filter(MessageRow.id == message_id, MessageRow.tenant_id == tenant_id).first()
    if not row:
        raise api_error("NOT_FOUND", "Message not found", 404)
    return ok(_row_to_out(row))
