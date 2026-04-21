"""Leads endpoints.

Spec: spec/product/04-api.md — /leads
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from zer0.api._common import api_error, get_current_tenant_id, ok, paginated
from zer0.db import LeadRow, get_session

router = APIRouter(prefix="/leads")


class LeadOut(BaseModel):
    id: str
    tenant_id: str
    campaign_id: str
    stage: str
    name: str | None
    company: str | None
    url: str
    source: str
    score: float | None
    rationale: str | None
    rejection_reason: str | None
    detected_language: str | None
    contact_email: str | None
    contact_role: str | None
    created_at: datetime
    updated_at: datetime


class LeadPatch(BaseModel):
    stage: str | None = None
    contact_email: str | None = None
    contact_role: str | None = None


def _row_to_out(l: LeadRow) -> LeadOut:
    return LeadOut(
        id=l.id, tenant_id=l.tenant_id, campaign_id=l.campaign_id,
        stage=l.stage, name=l.name, company=l.company, url=l.url, source=l.source,
        score=float(l.score) if l.score is not None else None,
        rationale=l.rationale, rejection_reason=l.rejection_reason,
        detected_language=l.detected_language, contact_email=l.contact_email,
        contact_role=l.contact_role, created_at=l.created_at, updated_at=l.updated_at,
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
    for field, value in body.model_dump(exclude_none=True).items():
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
