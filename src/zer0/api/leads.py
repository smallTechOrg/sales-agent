"""Leads endpoints.

Spec: spec/product/09-api.md — /leads
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from zer0.api._common import api_error, get_current_tenant_id, ok, paginated
from zer0.db import LeadRow, get_session

router = APIRouter(prefix="/leads")


class LeadOut(BaseModel):
    id: str
    tenant_id: str
    campaign_id: str
    link_id: str | None
    stage: str
    company_name: str | None
    domain: str | None
    industry: str | None
    headcount_range: str | None
    business_type: str | None
    research_summary: str | None
    signals: list | None
    score: float | None
    per_criterion_scores: list | None
    rationale: str | None
    rejection_reason: str | None
    detected_language: str | None
    blocked_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LeadPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: str | None = None
    blocked: bool | None = None


def _row_to_out(l: LeadRow) -> LeadOut:
    return LeadOut(
        id=l.id,
        tenant_id=l.tenant_id,
        campaign_id=l.campaign_id,
        link_id=l.link_id,
        stage=l.stage,
        company_name=l.company_name,
        domain=l.domain,
        industry=l.industry,
        headcount_range=l.headcount_range,
        business_type=l.business_type,
        research_summary=l.research_summary,
        signals=l.signals,
        score=float(l.score) if l.score is not None else None,
        per_criterion_scores=l.per_criterion_scores,
        rationale=l.rationale,
        rejection_reason=l.rejection_reason,
        detected_language=l.detected_language,
        blocked_at=l.blocked_at,
        created_at=l.created_at,
        updated_at=l.updated_at,
    )


def _get_or_404(lead_id: str, tenant_id: str, session: Session) -> LeadRow:
    row = (
        session.query(LeadRow)
        .filter(LeadRow.id == lead_id, LeadRow.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise api_error("NOT_FOUND", "Lead not found", 404)
    return row


@router.get("")
def list_leads(
    campaign_id: str | None = None,
    stage: str | None = None,
    cursor: str | None = None,
    limit: int = 50,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    q = session.query(LeadRow).filter(LeadRow.tenant_id == tenant_id)
    if campaign_id:
        q = q.filter(LeadRow.campaign_id == campaign_id)
    if stage:
        q = q.filter(LeadRow.stage == stage)
    if cursor:
        q = q.filter(LeadRow.id > cursor)
    rows = q.order_by(LeadRow.id).limit(limit + 1).all()
    next_cur = rows[-1].id if len(rows) > limit else None
    return paginated([_row_to_out(r) for r in rows[:limit]], next_cur)


@router.get("/{lead_id}")
def get_lead(
    lead_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    return ok(_row_to_out(_get_or_404(lead_id, tenant_id, session)))


@router.patch("/{lead_id}")
def patch_lead(
    lead_id: str,
    body: LeadPatch,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    row = _get_or_404(lead_id, tenant_id, session)
    patch = body.model_dump(exclude_none=True)
    if "blocked" in patch:
        row.blocked_at = datetime.utcnow() if patch.pop("blocked") else None
    for field, value in patch.items():
        setattr(row, field, value)
    session.add(row)
    return ok(_row_to_out(row))


@router.post("/{lead_id}/trigger-followup", status_code=202)
def trigger_followup(
    lead_id: str,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    """Manually trigger a follow-up for a specific lead."""
    row = _get_or_404(lead_id, tenant_id, session)
    campaign_id = row.campaign_id

    def _run():
        from zer0.graph.runner import run_campaign
        run_campaign(campaign_id=campaign_id, tenant_id=tenant_id)

    background_tasks.add_task(_run)
    return ok({"triggered": True, "lead_id": lead_id})
