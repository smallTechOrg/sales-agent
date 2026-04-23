"""Lead pipeline domain models.

Spec: spec/product/07-data-model.md — leads table
Spec: spec/product/10-agent-graph.md — AgentState
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LeadStage(str, Enum):
    prospect = "prospect"
    research = "research"
    qualification = "qualification"
    people = "people"
    approval = "approval"
    outreach = "outreach"
    first_contact = "first_contact"
    no_contact = "no_contact"
    rejected = "rejected"
    blocked = "blocked"


class PerCriterionScore(BaseModel):
    criterion_name: str
    score: float  # 0–100


class Lead(BaseModel):
    id: str
    tenant_id: str
    campaign_id: str
    link_id: str | None = None
    company_id: str | None = None
    stage: LeadStage = LeadStage.prospect
    company_name: str | None = None
    domain: str | None = None
    industry: str | None = None
    headcount_range: str | None = None
    business_type: str | None = None
    research_summary: str | None = None
    signals: list[str] = Field(default_factory=list)
    score: float | None = None
    per_criterion_scores: list[PerCriterionScore] = Field(default_factory=list)
    rationale: str | None = None
    rejection_reason: str | None = None
    detected_language: str | None = None  # ISO 639-1; set by detect_language tool
    blocked_at: datetime | None = None
    last_researched_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
