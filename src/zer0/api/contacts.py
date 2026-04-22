"""Contacts endpoints.

Spec: spec/product/09-api.md — /contacts
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from zer0.api._common import api_error, get_current_tenant_id, ok, paginated
from zer0.db import get_session
from zer0.db.models import ContactRow


class ContactPatch(BaseModel):
    approved_for_outreach: bool | None = None
    outreach_stopped: bool | None = None

router = APIRouter(prefix="/contacts")


class ContactOut(BaseModel):
    id: str
    tenant_id: str
    lead_id: str
    customer_id: str | None
    first_name: str | None
    last_name: str | None
    full_name: str | None
    email: str | None
    phone: str | None
    role: str | None
    linkedin_url: str | None
    approved_for_outreach: bool
    outreach_stopped: bool
    created_at: datetime
    updated_at: datetime


def _row_to_out(row: ContactRow) -> ContactOut:
    return ContactOut(
        id=row.id,
        tenant_id=row.tenant_id,
        lead_id=row.lead_id,
        customer_id=row.customer_id,
        first_name=row.first_name,
        last_name=row.last_name,
        full_name=row.full_name,
        email=row.email,
        phone=row.phone,
        role=row.role,
        linkedin_url=row.linkedin_url,
        approved_for_outreach=row.approved_for_outreach,
        outreach_stopped=row.outreach_stopped,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("")
def list_contacts(
    cursor: str | None = None,
    limit: int = 50,
    customer_id: str | None = None,
    lead_id: str | None = None,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    if limit > 200:
        raise api_error("INVALID_REQUEST", "limit must be ≤ 200")

    q = (
        session.query(ContactRow)
        .filter(ContactRow.tenant_id == tenant_id)
        .order_by(ContactRow.created_at.desc())
    )
    if customer_id:
        q = q.filter(ContactRow.customer_id == customer_id)
    if lead_id:
        q = q.filter(ContactRow.lead_id == lead_id)
    if cursor:
        q = q.filter(ContactRow.id < cursor)

    rows = q.limit(limit + 1).all()
    has_more = len(rows) > limit
    items = [_row_to_out(r) for r in rows[:limit]]
    return paginated(items, items[-1].id if has_more else None)


@router.get("/{contact_id}")
def get_contact(
    contact_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    row = (
        session.query(ContactRow)
        .filter(ContactRow.id == contact_id, ContactRow.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise api_error("NOT_FOUND", "Contact not found", 404)
    return ok(_row_to_out(row))


@router.patch("/{contact_id}")
def patch_contact(
    contact_id: str,
    body: ContactPatch,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """Operator-facing: toggle approved_for_outreach / outreach_stopped.

    Spec: spec/product/04-capabilities/08-approval.md — Contact approval
    """
    row = (
        session.query(ContactRow)
        .filter(ContactRow.id == contact_id, ContactRow.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise api_error("NOT_FOUND", "Contact not found", 404)
    if body.approved_for_outreach is not None:
        row.approved_for_outreach = body.approved_for_outreach
    if body.outreach_stopped is not None:
        row.outreach_stopped = body.outreach_stopped
    session.add(row)
    session.commit()
    session.refresh(row)
    return ok(_row_to_out(row))
