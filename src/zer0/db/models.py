"""SQLAlchemy ORM models.

Spec: spec/product/03-db-schema.md
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
    retargeting_cooldown_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    default_approval_mode: Mapped[str] = mapped_column(String(64), nullable=False, default="approve_all")
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
# leads
# ---------------------------------------------------------------------------

class LeadRow(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    campaign_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("campaigns.id"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="discovered")
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    enriched_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    per_criterion_scores: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    blocked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    discovered_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_role: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now)

    campaign: Mapped[CampaignRow] = relationship(back_populates="leads")
    messages: Mapped[list[MessageRow]] = relationship(back_populates="lead")
    replies: Mapped[list[ReplyRow]] = relationship(back_populates="lead")
    events: Mapped[list[EventRow]] = relationship(back_populates="lead")


# ---------------------------------------------------------------------------
# messages
# ---------------------------------------------------------------------------

class MessageRow(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    campaign_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("campaigns.id"), nullable=False, index=True)
    lead_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("leads.id"), nullable=False, index=True)
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
    replies: Mapped[list[ReplyRow]] = relationship(back_populates="message")


# ---------------------------------------------------------------------------
# replies
# ---------------------------------------------------------------------------

class ReplyRow(Base):
    __tablename__ = "replies"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("leads.id"), nullable=False, index=True)
    message_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("messages.id"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str | None] = mapped_column(String(16), nullable=True)
    received_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    lead: Mapped[LeadRow] = relationship(back_populates="replies")
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
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    config_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    lead: Mapped[LeadRow | None] = relationship(back_populates="events")
