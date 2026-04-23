"""People endpoints.

Spec: spec/product/09-api.md — /people
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from zer0.api._common import api_error, get_current_tenant_id, ok, paginated
from zer0.db import get_session
from zer0.db.models import LeadRow, LinkRow, PersonRow


class PersonPatch(BaseModel):
    approved_for_outreach: bool | None = None
    outreach_stopped: bool | None = None

router = APIRouter(prefix="/people")


class PersonSourceLink(BaseModel):
    id: str
    url: str
    source: str
    page_excerpt: str | None
    scraped_at: datetime | None


class PersonOut(BaseModel):
    id: str
    tenant_id: str
    lead_id: str
    company_id: str | None
    first_name: str | None
    last_name: str | None
    full_name: str | None
    email: str | None
    phone: str | None
    role: str | None
    linkedin_url: str | None
    approved_for_outreach: bool
    outreach_stopped: bool
    source_link: PersonSourceLink | None
    created_at: datetime
    updated_at: datetime


def _row_to_out(row: PersonRow, link: LinkRow | None = None) -> PersonOut:
    source_link = None
    if link:
        source_link = PersonSourceLink(
            id=link.id,
            url=link.url,
            source=link.source,
            page_excerpt=link.page_excerpt,
            scraped_at=link.scraped_at,
        )
    return PersonOut(
        id=row.id,
        tenant_id=row.tenant_id,
        lead_id=row.lead_id,
        company_id=row.company_id,
        first_name=row.first_name,
        last_name=row.last_name,
        full_name=row.full_name,
        email=row.email,
        phone=row.phone,
        role=row.role,
        linkedin_url=row.linkedin_url,
        approved_for_outreach=row.approved_for_outreach,
        outreach_stopped=row.outreach_stopped,
        source_link=source_link,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _fetch_link(person: PersonRow, session: Session) -> LinkRow | None:
    lead = session.query(LeadRow).filter(LeadRow.id == person.lead_id).first()
    if not lead or not lead.link_id:
        return None
    return session.query(LinkRow).filter(LinkRow.id == lead.link_id).first()


@router.get("")
def list_people(
    cursor: str | None = None,
    limit: int = 50,
    company_id: str | None = None,
    lead_id: str | None = None,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    if limit > 200:
        raise api_error("INVALID_REQUEST", "limit must be ≤ 200")

    q = (
        session.query(PersonRow)
        .filter(PersonRow.tenant_id == tenant_id)
        .order_by(PersonRow.created_at.desc())
    )
    if company_id:
        q = q.filter(PersonRow.company_id == company_id)
    if lead_id:
        q = q.filter(PersonRow.lead_id == lead_id)
    if cursor:
        q = q.filter(PersonRow.id < cursor)

    rows = q.limit(limit + 1).all()
    has_more = len(rows) > limit
    page = rows[:limit]
    items = [_row_to_out(r, _fetch_link(r, session)) for r in page]
    return paginated(items, items[-1].id if has_more else None)


@router.get("/{person_id}")
def get_person(
    person_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    row = (
        session.query(PersonRow)
        .filter(PersonRow.id == person_id, PersonRow.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise api_error("NOT_FOUND", "Person not found", 404)
    return ok(_row_to_out(row, _fetch_link(row, session)))


@router.patch("/{person_id}")
def patch_person(
    person_id: str,
    body: PersonPatch,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """Operator-facing: toggle approved_for_outreach / outreach_stopped.

    Spec: spec/product/04-capabilities/08-approval.md — Person approval
    """
    row = (
        session.query(PersonRow)
        .filter(PersonRow.id == person_id, PersonRow.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise api_error("NOT_FOUND", "Person not found", 404)
    if body.approved_for_outreach is not None:
        row.approved_for_outreach = body.approved_for_outreach
    if body.outreach_stopped is not None:
        row.outreach_stopped = body.outreach_stopped
    session.add(row)
    session.commit()
    session.refresh(row)
    return ok(_row_to_out(row))
