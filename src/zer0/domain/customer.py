"""Customer domain model.

Spec: spec/product/07-data-model.md — customers table

A Customer is a tenant-wide persistent record for a company identified
across one or more campaigns. Knowledge is cumulative: research_summary
and signals are appended on each agent run; humans can supplement via
the notes field.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Customer(BaseModel):
    id: str
    tenant_id: str
    domain: str
    company_name: Optional[str] = None
    industry: Optional[str] = None
    headcount_range: Optional[str] = None
    business_type: Optional[str] = None
    research_summary: Optional[str] = None
    signals: list[str] = []
    notes: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_enriched_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
