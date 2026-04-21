"""Initial schema — all tables.

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("google_oauth_token_enc", sa.Text, nullable=True),
        sa.Column("whatsapp_api_key_enc", sa.Text, nullable=True),
        sa.Column("slack_webhook_url_enc", sa.Text, nullable=True),
        sa.Column("notification_rules", postgresql.JSONB, nullable=True),
        sa.Column("retargeting_cooldown_days", sa.Integer, nullable=False, server_default="90"),
        sa.Column("default_approval_mode", sa.String(64), nullable=False, server_default="approve_all"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "offerings",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("value_proposition", sa.Text, nullable=True),
        sa.Column("pain_points", sa.ARRAY(sa.Text), nullable=True),
        sa.Column("discovery_config", postgresql.JSONB, nullable=True),
        sa.Column("icp", postgresql.JSONB, nullable=True),
        sa.Column("qualification_config", postgresql.JSONB, nullable=True),
        sa.Column("outreach_config", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_offerings_tenant_id", "offerings", ["tenant_id"])

    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("offering_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("discovery_override", postgresql.JSONB, nullable=True),
        sa.Column("icp_override", postgresql.JSONB, nullable=True),
        sa.Column("qualification_override", postgresql.JSONB, nullable=True),
        sa.Column("outreach_override", postgresql.JSONB, nullable=True),
        sa.Column("schedule", sa.Text, nullable=True),
        sa.Column("volume_cap", sa.Integer, nullable=True),
        sa.Column("approval_mode", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["offering_id"], ["offerings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_campaigns_tenant_id", "campaigns", ["tenant_id"])
    op.create_index("ix_campaigns_offering_id", "campaigns", ["offering_id"])

    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False, server_default="discovered"),
        sa.Column("name", sa.Text, nullable=True),
        sa.Column("company", sa.Text, nullable=True),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("enriched_data", postgresql.JSONB, nullable=True),
        sa.Column("score", sa.Numeric, nullable=True),
        sa.Column("per_criterion_scores", postgresql.JSONB, nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("detected_language", sa.String(8), nullable=True),
        sa.Column("blocked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("discovered_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("contact_email", sa.Text, nullable=True),
        sa.Column("contact_phone", sa.Text, nullable=True),
        sa.Column("contact_role", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leads_tenant_id", "leads", ["tenant_id"])
    op.create_index("ix_leads_campaign_id", "leads", ["campaign_id"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("subject", sa.Text, nullable=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("personalisation_notes", sa.Text, nullable=True),
        sa.Column("config_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("sequence_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="drafted"),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("external_message_id", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_tenant_id", "messages", ["tenant_id"])
    op.create_index("ix_messages_campaign_id", "messages", ["campaign_id"])
    op.create_index("ix_messages_lead_id", "messages", ["lead_id"])

    op.create_table(
        "replies",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("sentiment", sa.String(16), nullable=True),
        sa.Column("received_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_replies_tenant_id", "replies", ["tenant_id"])
    op.create_index("ix_replies_lead_id", "replies", ["lead_id"])
    op.create_index("ix_replies_message_id", "replies", ["message_id"])

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("event_type", sa.Text, nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column("config_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_tenant_id", "events", ["tenant_id"])
    op.create_index("ix_events_campaign_id", "events", ["campaign_id"])
    op.create_index("ix_events_lead_id", "events", ["lead_id"])


def downgrade() -> None:
    op.drop_table("events")
    op.drop_table("replies")
    op.drop_table("messages")
    op.drop_table("leads")
    op.drop_table("campaigns")
    op.drop_table("offerings")
    op.drop_table("tenants")
