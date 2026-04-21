"""Campaigns endpoints.

Spec: spec/product/09-api.md — /campaigns
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from zer0.api._common import api_error, get_current_tenant_id, ok, paginated
from zer0.db import CampaignRow, get_session

router = APIRouter(prefix="/campaigns")


class CampaignOut(BaseModel):
    id: str
    tenant_id: str
    offering_id: str
    name: str
    schedule: str | None
    volume_cap: int | None
    approval_mode: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class CampaignCreate(BaseModel):
    offering_id: str
    name: str
    schedule: str | None = None
    volume_cap: int | None = None
    approval_mode: str | None = None
    discovery_override: dict | None = None
    icp_override: dict | None = None
    qualification_override: dict | None = None
    outreach_override: dict | None = None


class CampaignPatch(BaseModel):
    name: str | None = None
    schedule: str | None = None
    volume_cap: int | None = None
    approval_mode: str | None = None
    status: str | None = None
    discovery_override: dict | None = None
    icp_override: dict | None = None
    qualification_override: dict | None = None
    outreach_override: dict | None = None


def _row_to_out(c: CampaignRow) -> CampaignOut:
    return CampaignOut(
        id=c.id, tenant_id=c.tenant_id, offering_id=c.offering_id,
        name=c.name, schedule=c.schedule, volume_cap=c.volume_cap,
        approval_mode=c.approval_mode, status=c.status,
        created_at=c.created_at, updated_at=c.updated_at,
    )


def _get_or_404(campaign_id: str, tenant_id: str, session: Session) -> CampaignRow:
    c = (
        session.query(CampaignRow)
        .filter(CampaignRow.id == campaign_id, CampaignRow.tenant_id == tenant_id, CampaignRow.deleted_at.is_(None))
        .first()
    )
    if not c:
        raise api_error("NOT_FOUND", "Campaign not found", 404)
    return c


@router.get("")
def list_campaigns(
    cursor: str | None = None,
    limit: int = 50,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    q = session.query(CampaignRow).filter(CampaignRow.tenant_id == tenant_id, CampaignRow.deleted_at.is_(None))
    if cursor:
        q = q.filter(CampaignRow.id > cursor)
    rows = q.order_by(CampaignRow.id).limit(limit + 1).all()
    next_cur = rows[-1].id if len(rows) > limit else None
    return paginated([_row_to_out(r) for r in rows[:limit]], next_cur)


@router.post("", status_code=201)
def create_campaign(
    body: CampaignCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    row = CampaignRow(tenant_id=tenant_id, **body.model_dump())
    session.add(row)
    session.flush()
    return ok(_row_to_out(row))


@router.get("/{campaign_id}")
def get_campaign(
    campaign_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    return ok(_row_to_out(_get_or_404(campaign_id, tenant_id, session)))


@router.patch("/{campaign_id}")
def patch_campaign(
    campaign_id: str,
    body: CampaignPatch,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    row = _get_or_404(campaign_id, tenant_id, session)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    session.add(row)
    return ok(_row_to_out(row))


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(
    campaign_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    row = _get_or_404(campaign_id, tenant_id, session)
    row.deleted_at = datetime.now(tz=timezone.utc)
    session.add(row)


@router.post("/{campaign_id}/trigger", status_code=202)
def trigger_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """Manually trigger a campaign run in the background.

    Spec: spec/product/09-api.md — POST /campaigns/{id}/trigger
    Returns run_id so the caller can poll GET /events for progress.
    """
    import uuid as _uuid

    _get_or_404(campaign_id, tenant_id, session)  # validates existence + tenant isolation
    run_id = str(_uuid.uuid4())

    def _run():
        from zer0.graph.runner import run_campaign
        run_campaign(campaign_id=campaign_id, tenant_id=tenant_id, run_id=run_id)

    background_tasks.add_task(_run)
    return ok({"run_id": run_id, "message": "Campaign run queued."})
