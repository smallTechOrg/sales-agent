"""Events endpoint.

Spec: spec/product/04-api.md — /events
Append-only audit log — read-only API.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from zer0.api._common import get_current_tenant_id, paginated
from zer0.db import EventRow, get_session

router = APIRouter(prefix="/events")


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
        q = q.filter(EventRow.id > cursor)
    rows = q.order_by(EventRow.created_at.desc()).limit(limit + 1).all()
    next_cur = rows[-1].id if len(rows) > limit else None
    items = [
        EventOut(id=r.id, tenant_id=r.tenant_id, campaign_id=r.campaign_id,
                 lead_id=r.lead_id, event_type=r.event_type, payload=r.payload,
                 created_at=r.created_at)
        for r in rows[:limit]
    ]
    return paginated(items, next_cur)
