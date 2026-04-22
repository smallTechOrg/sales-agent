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
    campaign_id: str
    url: str
    source: LinkSource
    page_text: str | None = None
    scraped_at: datetime | None = None
    identified_at: datetime | None = None
    created_at: datetime | None = None
