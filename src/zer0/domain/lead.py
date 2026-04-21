"""Lead pipeline domain models.

Spec: spec/product/02-architecture.md — Domain models / Lead pipeline models
Spec: spec/product/03-db-schema.md — leads table
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class LeadStage(str, Enum):
    discovered = "discovered"
    enriched = "enriched"
    qualified = "qualified"
    rejected = "rejected"
    approved = "approved"
    outreach_active = "outreach_active"
    responded = "responded"
    blocked = "blocked"


class LeadSource(str, Enum):
    linkedin = "linkedin"
    web = "web"
    directory = "directory"


class RawLead(BaseModel):
    id: str
    campaign_id: str
    tenant_id: str
    name: str | None = None
    company: str | None = None
    url: str
    source: LeadSource


class EnrichedLead(RawLead):
    company_summary: str | None = None
    role_summary: str | None = None
    recent_signals: list[str] = Field(default_factory=list)
    detected_language: str | None = None  # ISO 639-1; set by detect_language tool
    contact_email: str | None = None
    contact_phone: str | None = None
    contact_role: str | None = None


class PerCriterionScore(BaseModel):
    criterion_name: str
    score: float  # 0–100


class QualifiedLead(EnrichedLead):
    score: float  # 0–100
    per_criterion_scores: list[PerCriterionScore]
    rationale: str


class RejectedLead(EnrichedLead):
    rejection_reason: str
    per_criterion_scores: list[PerCriterionScore]
