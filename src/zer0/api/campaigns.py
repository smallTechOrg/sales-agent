"""Campaigns endpoints.

Spec: spec/product/09-api.md — /campaigns
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from zer0.api._common import api_error, get_current_tenant_id, ok, paginated
from zer0.db import CampaignRow, CampaignRunRow, LeadRow, LinkRow, MessageRow, ReplyRow, get_session

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


class RunOut(BaseModel):
    id: str
    campaign_id: str
    tenant_id: str
    status: str
    current_node: str | None
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None
    input_tokens: int
    output_tokens: int
    total_tokens: int
    llm_call_count: int
    estimated_cost_usd: float
    created_at: datetime


def _row_to_out(c: CampaignRow) -> CampaignOut:
    return CampaignOut(
        id=c.id, tenant_id=c.tenant_id, offering_id=c.offering_id,
        name=c.name, schedule=c.schedule, volume_cap=c.volume_cap,
        approval_mode=c.approval_mode, status=c.status,
        created_at=c.created_at, updated_at=c.updated_at,
    )


def _run_to_out(r: CampaignRunRow) -> RunOut:
    return RunOut(
        id=r.id, campaign_id=r.campaign_id, tenant_id=r.tenant_id,
        status=r.status, current_node=r.current_node,
        started_at=r.started_at, finished_at=r.finished_at,
        error=r.error, created_at=r.created_at,
        input_tokens=r.input_tokens or 0,
        output_tokens=r.output_tokens or 0,
        total_tokens=r.total_tokens or 0,
        llm_call_count=r.llm_call_count or 0,
        estimated_cost_usd=float(r.estimated_cost_usd or 0),
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
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """Manually trigger a campaign run in a dedicated thread pool.

    Spec: spec/product/09-api.md — Threading model
    Returns immediately (202) with run_id. Poll GET /campaigns/{id}/runs/{run_id}
    for live status. The uvicorn thread is never blocked by agent execution.
    Returns 409 if a run is already active for this campaign.
    """
    from zer0.graph import runner_service

    _get_or_404(campaign_id, tenant_id, session)
    run_id = str(uuid.uuid4())
    try:
        runner_service.submit(campaign_id=campaign_id, tenant_id=tenant_id, run_id=run_id)
    except RuntimeError as exc:
        raise api_error("CONFLICT", str(exc), 409)
    return ok({"run_id": run_id, "message": "Campaign run queued."})


@router.get("/{campaign_id}/stats")
def campaign_stats(
    campaign_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """Return live aggregate counts for a campaign.

    Spec: spec/product/09-api.md — GET /campaigns/{id}/stats
    Counts are read fresh from DB on every call.
    """
    _get_or_404(campaign_id, tenant_id, session)

    total_links = (
        session.query(func.count(LinkRow.id))
        .filter(LinkRow.tenant_id == tenant_id, LinkRow.campaign_id == campaign_id)
        .scalar() or 0
    )

    stage_rows = (
        session.query(LeadRow.stage, func.count(LeadRow.id))
        .filter(
            LeadRow.tenant_id == tenant_id,
            LeadRow.campaign_id == campaign_id,
            LeadRow.blocked_at.is_(None),
        )
        .group_by(LeadRow.stage)
        .all()
    )
    by_stage = {stage: count for stage, count in stage_rows}
    total_leads = sum(by_stage.values())

    messages_sent = (
        session.query(func.count(MessageRow.id))
        .filter(
            MessageRow.tenant_id == tenant_id,
            MessageRow.campaign_id == campaign_id,
            MessageRow.status == "sent",
        )
        .scalar() or 0
    )

    replies_received = (
        session.query(func.count(ReplyRow.id))
        .filter(ReplyRow.tenant_id == tenant_id, ReplyRow.lead_id.in_(
            session.query(LeadRow.id).filter(
                LeadRow.tenant_id == tenant_id,
                LeadRow.campaign_id == campaign_id,
            )
        ))
        .scalar() or 0
    )

    return ok({
        "campaign_id": campaign_id,
        "total_links": total_links,
        "total_leads": total_leads,
        "by_stage": by_stage,
        "messages_sent": messages_sent,
        "replies_received": replies_received,
    })


@router.get("/{campaign_id}/runs")
def list_runs(
    campaign_id: str,
    cursor: str | None = None,
    limit: int = 20,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """List all agent runs for a campaign, newest first.

    Spec: spec/product/09-api.md — GET /campaigns/{id}/runs
    """
    _get_or_404(campaign_id, tenant_id, session)
    q = (
        session.query(CampaignRunRow)
        .filter(CampaignRunRow.campaign_id == campaign_id, CampaignRunRow.tenant_id == tenant_id)
        .order_by(CampaignRunRow.created_at.desc())
    )
    if cursor:
        q = q.filter(CampaignRunRow.id < cursor)
    rows = q.limit(limit + 1).all()
    has_more = len(rows) > limit
    items = [_run_to_out(r) for r in rows[:limit]]
    return paginated(items, items[-1].id if has_more else None)


@router.get("/{campaign_id}/runs/{run_id}")
def get_run(
    campaign_id: str,
    run_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """Get the status of a specific agent run.

    Spec: spec/product/09-api.md — GET /campaigns/{id}/runs/{run_id}
    """
    _get_or_404(campaign_id, tenant_id, session)
    row = (
        session.query(CampaignRunRow)
        .filter(
            CampaignRunRow.id == run_id,
            CampaignRunRow.campaign_id == campaign_id,
            CampaignRunRow.tenant_id == tenant_id,
        )
        .first()
    )
    if not row:
        raise api_error("NOT_FOUND", "Run not found", 404)
    return ok(_run_to_out(row))
