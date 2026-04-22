"""Configuration hierarchy domain models.

Spec: spec/product/02-architecture.md — Domain models / Configuration hierarchy
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class ApprovalMode(str, Enum):
    full_auto = "full_auto"
    approve_qualify = "approve_qualify"
    approve_messages = "approve_messages"
    approve_all = "approve_all"


class Channel(str, Enum):
    email = "email"
    whatsapp = "whatsapp"


class DiscoverySource(str, Enum):
    linkedin = "linkedin"
    web = "web"
    directory = "directory"


class CompanySizeRange(BaseModel):
    min: Annotated[int, Field(ge=1)]
    max: Annotated[int, Field(ge=1)]


class DiscoveryConfig(BaseModel):
    sources: list[DiscoverySource]
    query_templates: list[str]
    geography: list[str]
    volume_per_run: Annotated[int, Field(ge=1, le=1000)]


class ICP(BaseModel):
    target_industries: list[str]
    target_roles: list[str]
    company_size_range: CompanySizeRange
    geography: list[str]
    keywords: list[str]
    negative_keywords: list[str]


class RubricCriterion(BaseModel):
    name: str
    description: str
    weight: Annotated[float, Field(gt=0.0, le=1.0)]


class QualificationConfig(BaseModel):
    rubric_criteria: Annotated[list[RubricCriterion], Field(min_length=1)]
    score_threshold: Annotated[float, Field(ge=0.0, le=100.0)]
    disqualifying_signals: list[str]


class OutreachTemplates(BaseModel):
    first_touch: str
    follow_up_1: str | None = None
    follow_up_2: str | None = None
    follow_up_3: str | None = None


class OutreachConfig(BaseModel):
    channels_enabled: Annotated[list[Channel], Field(min_length=1)]
    tone: str
    language_default: str  # ISO 639-1
    templates: OutreachTemplates
    follow_up_count: Annotated[int, Field(ge=0, le=10)]
    follow_up_spacing_days: Annotated[int, Field(ge=1)]
    send_schedule: str  # e.g. "09:00-17:00 Mon-Fri"


class ResolvedConfig(BaseModel):
    """Fully merged config — the only config object the agent reads during a run.

    Spec: spec/product/02-architecture.md — Configuration resolution
    Never persisted. Computed fresh on every agent tick by ConfigResolver.
    """

    tenant_id: str
    campaign_id: str
    offering_id: str

    # Offering metadata
    offering_name: str
    value_proposition: str
    pain_points: list[str]

    # Merged sub-configs
    discovery_config: DiscoveryConfig
    icp: ICP
    qualification_config: QualificationConfig
    outreach_config: OutreachConfig

    # Campaign-level settings
    approval_mode: ApprovalMode
    volume_cap: int | None = None
    schedule: str | None = None

    # Tenant-level credentials (encrypted; decrypted at runtime by tools)
    google_oauth_token_enc: str | None = None
    whatsapp_api_key_enc: str | None = None
    slack_webhook_url: str | None = None  # decrypted webhook URL
