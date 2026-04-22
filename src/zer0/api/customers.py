"""Customers endpoints.

Spec: spec/product/09-api.md — /customers
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from zer0.api._common import api_error, get_current_tenant_id, ok, paginated
from zer0.db import CustomerRow, LeadRow, LinkLeadsRow, LinkRow, get_session

router = APIRouter(prefix="/customers")


class SourceLinkOut(BaseModel):
    id: str
    url: str
    campaign_id: str | None
    scraped_at: datetime | None


class CustomerOut(BaseModel):
    id: str
    tenant_id: str
    domain: str
    company_name: str | None
    industry: str | None
    headcount_range: str | None
    business_type: str | None
    research_summary: str | None
    signals: list | None
    notes: str | None
    first_seen_at: datetime | None
    last_enriched_at: datetime | None
    source_links: list[SourceLinkOut]
    created_at: datetime
    updated_at: datetime


class CustomerPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str | None = None
    industry: str | None = None
    headcount_range: str | None = None
    business_type: str | None = None
    notes: str | None = None


def _row_to_out(row: CustomerRow, source_links: list[LinkRow] | None = None) -> CustomerOut:
    return CustomerOut(
        id=row.id,
        tenant_id=row.tenant_id,
        domain=row.domain,
        company_name=row.company_name,
        industry=row.industry,
        headcount_range=row.headcount_range,
        business_type=row.business_type,
        research_summary=row.research_summary,
        signals=row.signals,
        notes=row.notes,
        first_seen_at=row.first_seen_at,
        last_enriched_at=row.last_enriched_at,
        source_links=[
            SourceLinkOut(id=l.id, url=l.url, campaign_id=l.campaign_id, scraped_at=l.scraped_at)
            for l in (source_links or [])
        ],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _get_or_404(customer_id: str, tenant_id: str, session: Session) -> CustomerRow:
    row = (
        session.query(CustomerRow)
        .filter(CustomerRow.id == customer_id, CustomerRow.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise api_error("NOT_FOUND", "Customer not found", 404)
    return row


@router.get("")
def list_customers(
    cursor: str | None = None,
    limit: int = 50,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    if limit > 200:
        raise api_error("INVALID_REQUEST", "limit must be ≤ 200")

    q = (
        session.query(CustomerRow)
        .filter(CustomerRow.tenant_id == tenant_id)
        .order_by(CustomerRow.last_enriched_at.desc().nullslast(), CustomerRow.created_at.desc())
    )
    if cursor:
        q = q.filter(CustomerRow.id < cursor)

    rows = q.limit(limit + 1).all()
    has_more = len(rows) > limit
    items = [_row_to_out(r) for r in rows[:limit]]
    next_cursor = items[-1].id if has_more else None
    return paginated(items, next_cursor)


@router.get("/{customer_id}")
def get_customer(
    customer_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    row = _get_or_404(customer_id, tenant_id, session)
    source_links = (
        session.query(LinkRow)
        .join(LinkLeadsRow, LinkLeadsRow.link_id == LinkRow.id)
        .join(LeadRow, LeadRow.id == LinkLeadsRow.lead_id)
        .filter(
            LeadRow.customer_id == customer_id,
            LeadRow.tenant_id == tenant_id,
            LinkRow.tenant_id == tenant_id,
        )
        .distinct()
        .all()
    )
    return ok(_row_to_out(row, source_links=source_links))


@router.patch("/{customer_id}")
def patch_customer(
    customer_id: str,
    body: CustomerPatch,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    row = _get_or_404(customer_id, tenant_id, session)
    update = body.model_dump(exclude_unset=True)
    for field, value in update.items():
        setattr(row, field, value)
    session.commit()
    session.refresh(row)
    return ok(_row_to_out(row))
