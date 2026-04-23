"""Events endpoint.

Spec: spec/product/04-api.md — /events
Append-only audit log — read-only API.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from zer0.api._common import api_error, get_current_tenant_id, paginated
from zer0.db import EventRow, get_session

router = APIRouter(prefix="/events")


def _encode_cursor(row: EventRow) -> str:
    return f"{row.created_at.isoformat()}|{row.id}"


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        created_at_raw, event_id = cursor.split("|", 1)
        return datetime.fromisoformat(created_at_raw), event_id
    except ValueError as exc:
        raise api_error("INVALID_REQUEST", "Invalid events cursor", 400) from exc


class EventOut(BaseModel):
    id: str
    tenant_id: str
    campaign_id: str | None
    lead_id: str | None
    event_type: str
    payload: dict | None
    created_at: datetime


@router.get("")
def list_events(
    campaign_id: str | None = None,
    lead_id: str | None = None,
    event_type: str | None = None,
    cursor: str | None = None,
    limit: int = 50,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    q = session.query(EventRow).filter(EventRow.tenant_id == tenant_id)
    if campaign_id:
        q = q.filter(EventRow.campaign_id == campaign_id)
    if lead_id:
        q = q.filter(EventRow.lead_id == lead_id)
    if event_type:
        q = q.filter(EventRow.event_type == event_type)
    if cursor:
        cursor_created_at, cursor_id = _decode_cursor(cursor)
        q = q.filter(
            or_(
                EventRow.created_at < cursor_created_at,
                and_(EventRow.created_at == cursor_created_at, EventRow.id < cursor_id),
            )
        )
    rows = q.order_by(EventRow.created_at.desc(), EventRow.id.desc()).limit(limit + 1).all()
    next_cur = _encode_cursor(rows[limit - 1]) if len(rows) > limit else None
    items = [
        EventOut(id=r.id, tenant_id=r.tenant_id, campaign_id=r.campaign_id,
                 lead_id=r.lead_id, event_type=r.event_type, payload=r.payload,
                 created_at=r.created_at)
        for r in rows[:limit]
    ]
    return paginated(items, next_cur)
