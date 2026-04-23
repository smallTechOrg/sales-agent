"""Link domain model.

Spec: spec/product/07-data-model.md — links table
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LinkSource(str, Enum):
    web = "web"
    linkedin = "linkedin"
    directory = "directory"


class Link(BaseModel):
    id: str
    tenant_id: str
    campaign_id: str | None = None  # first discoverer — nullable for tenant-scoped links
    url: str
    source: LinkSource
    page_text: str | None = None
    page_excerpt: str | None = None  # first ≤500 chars of page_text — safe to return in API responses
    scraped_at: datetime | None = None
    identified_at: datetime | None = None
    created_at: datetime | None = None
