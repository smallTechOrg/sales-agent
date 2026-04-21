"""Offerings endpoints.

Spec: spec/product/04-api.md — /offerings
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from zer0.api._common import api_error, get_current_tenant_id, ok, paginated
from zer0.db import OfferingRow, get_session

router = APIRouter(prefix="/offerings")


class OfferingOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str | None
    value_proposition: str | None
    pain_points: list[str] | None
    discovery_config: dict | None
    icp: dict | None
    qualification_config: dict | None
    outreach_config: dict | None
    created_at: datetime
    updated_at: datetime


class OfferingCreate(BaseModel):
    name: str
    description: str | None = None
    value_proposition: str | None = None
    pain_points: list[str] | None = None
    discovery_config: dict | None = None
    icp: dict | None = None
    qualification_config: dict | None = None
    outreach_config: dict | None = None


class OfferingPatch(BaseModel):
    name: str | None = None
    description: str | None = None
    value_proposition: str | None = None
    pain_points: list[str] | None = None
    discovery_config: dict | None = None
    icp: dict | None = None
    qualification_config: dict | None = None
    outreach_config: dict | None = None


def _row_to_out(o: OfferingRow) -> OfferingOut:
    return OfferingOut(
        id=o.id, tenant_id=o.tenant_id, name=o.name, description=o.description,
        value_proposition=o.value_proposition, pain_points=o.pain_points,
        discovery_config=o.discovery_config, icp=o.icp,
        qualification_config=o.qualification_config, outreach_config=o.outreach_config,
        created_at=o.created_at, updated_at=o.updated_at,
    )


def _get_or_404(offering_id: str, tenant_id: str, session: Session) -> OfferingRow:
    o = (
        session.query(OfferingRow)
        .filter(OfferingRow.id == offering_id, OfferingRow.tenant_id == tenant_id, OfferingRow.deleted_at.is_(None))
        .first()
    )
    if not o:
        raise api_error("NOT_FOUND", "Offering not found", 404)
    return o


@router.get("")
def list_offerings(
    cursor: str | None = None,
    limit: int = 50,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    q = session.query(OfferingRow).filter(OfferingRow.tenant_id == tenant_id, OfferingRow.deleted_at.is_(None))
    if cursor:
        q = q.filter(OfferingRow.id > cursor)
    rows = q.order_by(OfferingRow.id).limit(limit + 1).all()
    next_cur = rows[-1].id if len(rows) > limit else None
    return paginated([_row_to_out(r) for r in rows[:limit]], next_cur)


@router.post("", status_code=201)
def create_offering(
    body: OfferingCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    row = OfferingRow(tenant_id=tenant_id, **body.model_dump())
    session.add(row)
    session.flush()
    return ok(_row_to_out(row))


@router.get("/{offering_id}")
def get_offering(
    offering_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    return ok(_row_to_out(_get_or_404(offering_id, tenant_id, session)))


@router.patch("/{offering_id}")
def patch_offering(
    offering_id: str,
    body: OfferingPatch,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    row = _get_or_404(offering_id, tenant_id, session)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    session.add(row)
    return ok(_row_to_out(row))


@router.delete("/{offering_id}", status_code=204)
def delete_offering(
    offering_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    row = _get_or_404(offering_id, tenant_id, session)
    row.deleted_at = datetime.now(tz=timezone.utc)
    session.add(row)
