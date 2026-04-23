"""Company domain model.

Spec: spec/product/07-data-model.md — companies table

A Company is a tenant-wide persistent record for a company identified
across one or more campaigns. Knowledge is cumulative: research_summary
and signals are appended on each agent run; humans can supplement via
the notes field.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Company(BaseModel):
    id: str
    tenant_id: str
    domain: str
    company_name: Optional[str] = None
    industry: Optional[str] = None
    headcount_range: Optional[str] = None
    business_type: Optional[str] = None
    website: Optional[str] = None  # Canonical company website URL (fill-if-null)
    description: Optional[str] = None  # One-paragraph "what the company does" (fill-if-null)
    research_summary: Optional[str] = None
    signals: list[str] = []
    notes: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_enriched_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
