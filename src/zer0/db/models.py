"""SQLAlchemy ORM models.

Spec: spec/product/07-data-model.md
Every table carries tenant_id; no query should run without a tenant filter.
Sensitive credential columns are suffixed _enc (encrypted by the application).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    event,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    from datetime import timezone
    return datetime.now(tz=timezone.utc)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# tenants
# ---------------------------------------------------------------------------

class TenantRow(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    google_oauth_token_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    whatsapp_api_key_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    slack_webhook_url_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    notification_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    retargeting_cooldown_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    default_approval_mode: Mapped[str] = mapped_column(String(64), nullable=False, default="full_auto")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now)
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    offerings: Mapped[list[OfferingRow]] = relationship(back_populates="tenant")
    campaigns: Mapped[list[CampaignRow]] = relationship(back_populates="tenant")


# ---------------------------------------------------------------------------
# offerings
# ---------------------------------------------------------------------------

class OfferingRow(Base):
    __tablename__ = "offerings"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_proposition: Mapped[str | None] = mapped_column(Text, nullable=True)
    pain_points: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    discovery_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    icp: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    qualification_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    outreach_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now)
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    tenant: Mapped[TenantRow] = relationship(back_populates="offerings")
    campaigns: Mapped[list[CampaignRow]] = relationship(back_populates="offering")


# ---------------------------------------------------------------------------
# campaigns
# ---------------------------------------------------------------------------

class CampaignRow(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    offering_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("offerings.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    discovery_override: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    icp_override: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    qualification_override: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    outreach_override: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    schedule: Mapped[str | None] = mapped_column(Text, nullable=True)  # cron expression
    volume_cap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approval_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now)
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    tenant: Mapped[TenantRow] = relationship(back_populates="campaigns")
    offering: Mapped[OfferingRow] = relationship(back_populates="campaigns")
    leads: Mapped[list[LeadRow]] = relationship(back_populates="campaign")


# ---------------------------------------------------------------------------
# links  (raw URLs discovered by the discover node)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# companies  (tenant-wide persistent company knowledge base)
# ---------------------------------------------------------------------------

class CompanyRow(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(Text, nullable=False)
    company_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(Text, nullable=True)
    headcount_range: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    signals: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_enriched_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now)

    leads: Mapped[list[LeadRow]] = relationship(back_populates="company")
    people: Mapped[list[PersonRow]] = relationship(back_populates="company")


class LinkRow(Base):
    __tablename__ = "links"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    campaign_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True, index=True)  # first discoverer — nullable after migration
    url: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # web | linkedin | directory
    page_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    scrape_status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")  # pending | scraped | failed | blocked
    page_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    scraped_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    identified_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    leads: Mapped[list[LeadRow]] = relationship(back_populates="link")


# ---------------------------------------------------------------------------
# leads
# ---------------------------------------------------------------------------

class LeadRow(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    campaign_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("campaigns.id"), nullable=False, index=True)
    link_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("links.id"), nullable=True, index=True)
    company_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("companies.id"), nullable=True, index=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="prospect")
    company_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(Text, nullable=True)
    headcount_range: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    signals: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    per_criterion_scores: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    blocked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_researched_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now)

    campaign: Mapped[CampaignRow] = relationship(back_populates="leads")
    link: Mapped[LinkRow | None] = relationship(back_populates="leads")
    company: Mapped[CompanyRow | None] = relationship(back_populates="leads")
    people: Mapped[list[PersonRow]] = relationship(back_populates="lead")
    messages: Mapped[list[MessageRow]] = relationship(back_populates="lead")
    replies: Mapped[list[ReplyRow]] = relationship(back_populates="lead")
    events: Mapped[list[EventRow]] = relationship(back_populates="lead")


# ---------------------------------------------------------------------------
# people  (individual people at a lead's company)
# ---------------------------------------------------------------------------

class PersonRow(Base):
    __tablename__ = "people"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("leads.id"), nullable=False, index=True)
    company_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("companies.id"), nullable=True, index=True)
    first_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    seniority_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_maker_score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    approved_for_outreach: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    outreach_stopped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now)

    lead: Mapped[LeadRow] = relationship(back_populates="people")
    company: Mapped[CompanyRow | None] = relationship(back_populates="people")
    messages: Mapped[list[MessageRow]] = relationship(back_populates="person")
    replies: Mapped[list[ReplyRow]] = relationship(back_populates="person")


# ---------------------------------------------------------------------------
# messages
# ---------------------------------------------------------------------------

class MessageRow(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    campaign_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("campaigns.id"), nullable=False, index=True)
    lead_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("leads.id"), nullable=False, index=True)
    person_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("people.id"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    personalisation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    config_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="drafted")
    sent_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    external_message_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now)

    lead: Mapped[LeadRow] = relationship(back_populates="messages")
    person: Mapped[PersonRow | None] = relationship(back_populates="messages")
    replies: Mapped[list[ReplyRow]] = relationship(back_populates="message")


# ---------------------------------------------------------------------------
# replies
# ---------------------------------------------------------------------------

class ReplyRow(Base):
    __tablename__ = "replies"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("leads.id"), nullable=False, index=True)
    person_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("people.id"), nullable=True, index=True)
    message_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("messages.id"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str | None] = mapped_column(String(16), nullable=True)
    received_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    lead: Mapped[LeadRow] = relationship(back_populates="replies")
    person: Mapped[PersonRow | None] = relationship(back_populates="replies")
    message: Mapped[MessageRow | None] = relationship(back_populates="replies")


# ---------------------------------------------------------------------------
# events (append-only audit log)
# ---------------------------------------------------------------------------

class EventRow(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    campaign_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("campaigns.id"), nullable=True, index=True)
    lead_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("leads.id"), nullable=True, index=True)
    person_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("people.id"), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    config_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    lead: Mapped[LeadRow | None] = relationship(back_populates="events")


# ---------------------------------------------------------------------------
# link_leads  (junction: link ↔ lead ↔ campaign)
# ---------------------------------------------------------------------------

class LinkLeadsRow(Base):
    __tablename__ = "link_leads"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    link_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("links.id"), nullable=False, index=True)
    lead_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("leads.id"), nullable=False, index=True)
    campaign_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("campaigns.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)


# ---------------------------------------------------------------------------
# campaign_runs  (non-blocking agent run tracking)
# ---------------------------------------------------------------------------

class CampaignRunRow(Base):
    __tablename__ = "campaign_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    campaign_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("campaigns.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    current_node: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    llm_call_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
