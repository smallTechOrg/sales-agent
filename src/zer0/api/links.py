"""Links endpoints.

Spec: spec/product/09-api.md — /links
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from zer0.api._common import api_error, get_current_tenant_id, paginated
from zer0.db import LinkRow, get_session

router = APIRouter(prefix="/links")


class LinkOut(BaseModel):
    id: str
    tenant_id: str
    campaign_id: str
    url: str
    source: str
    scraped_at: datetime | None
    identified_at: datetime | None
    created_at: datetime


def _row_to_out(row: LinkRow) -> LinkOut:
    return LinkOut(
        id=row.id,
        tenant_id=row.tenant_id,
        campaign_id=row.campaign_id,
        url=row.url,
        source=row.source,
        scraped_at=row.scraped_at,
        identified_at=row.identified_at,
        created_at=row.created_at,
    )


@router.get("")
def list_links(
    campaign_id: str,
    cursor: str | None = None,
    limit: int = 50,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    if limit > 200:
        raise api_error("INVALID_REQUEST", "limit must be ≤ 200")

    q = (
        session.query(LinkRow)
        .filter(LinkRow.tenant_id == tenant_id, LinkRow.campaign_id == campaign_id)
        .order_by(LinkRow.created_at.desc())
    )
    if cursor:
        q = q.filter(LinkRow.id < cursor)

    rows = q.limit(limit + 1).all()
    has_more = len(rows) > limit
    items = [_row_to_out(r) for r in rows[:limit]]
    next_cursor = items[-1].id if has_more else None
    return paginated(items, next_cursor)
