"""Person domain model.

Spec: spec/product/07-data-model.md — people table
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Person(BaseModel):
    id: str
    tenant_id: str
    lead_id: str
    company_id: str | None = None  # set during get_people for cross-campaign dedup
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    linkedin_url: str | None = None
    approved_for_outreach: bool = False
    outreach_stopped: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
