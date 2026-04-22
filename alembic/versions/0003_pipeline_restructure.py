"""Restructure pipeline: add links + contacts tables, restructure leads.

Spec: spec/product/07-data-model.md

Revision ID: 0003_pipeline_restructure
Revises: 0002_fix_tenant_defaults
Create Date: 2026-04-22 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

revision: str = "0003_pipeline_restructure"
down_revision: str | None = "0002_fix_tenant_defaults"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # links table (new)
    # ------------------------------------------------------------------
    op.create_table(
        "links",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=False), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("campaign_id", UUID(as_uuid=False), sa.ForeignKey("campaigns.id"), nullable=False, index=True),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("page_text", sa.Text, nullable=True),
        sa.Column("scraped_at", TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ------------------------------------------------------------------
    # leads — remove old columns, add new columns
    # ------------------------------------------------------------------
    op.add_column("leads", sa.Column("link_id", UUID(as_uuid=False), sa.ForeignKey("links.id"), nullable=True))
    op.create_index("ix_leads_link_id", "leads", ["link_id"])
    op.add_column("leads", sa.Column("company_name", sa.Text, nullable=True))
    op.add_column("leads", sa.Column("domain", sa.Text, nullable=True))
    op.add_column("leads", sa.Column("industry", sa.Text, nullable=True))
    op.add_column("leads", sa.Column("headcount_range", sa.Text, nullable=True))
    op.add_column("leads", sa.Column("business_type", sa.Text, nullable=True))
    op.add_column("leads", sa.Column("research_summary", sa.Text, nullable=True))
    op.add_column("leads", sa.Column("signals", JSONB, nullable=True))
    op.add_column("leads", sa.Column("last_researched_at", TIMESTAMP(timezone=True), nullable=True))

    # update default stage value
    op.alter_column("leads", "stage", server_default="prospect")

    op.drop_column("leads", "name")
    op.drop_column("leads", "company")
    op.drop_column("leads", "url")
    op.drop_column("leads", "source")
    op.drop_column("leads", "enriched_data")
    op.drop_column("leads", "discovered_at")
    op.drop_column("leads", "contact_email")
    op.drop_column("leads", "contact_phone")
    op.drop_column("leads", "contact_role")

    # ------------------------------------------------------------------
    # contacts table (new)
    # ------------------------------------------------------------------
    op.create_table(
        "contacts",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=False), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("lead_id", UUID(as_uuid=False), sa.ForeignKey("leads.id"), nullable=False, index=True),
        sa.Column("first_name", sa.Text, nullable=True),
        sa.Column("last_name", sa.Text, nullable=True),
        sa.Column("full_name", sa.Text, nullable=True),
        sa.Column("email", sa.Text, nullable=True),
        sa.Column("phone", sa.Text, nullable=True),
        sa.Column("role", sa.Text, nullable=True),
        sa.Column("linkedin_url", sa.Text, nullable=True),
        sa.Column("approved_for_outreach", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("outreach_stopped", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ------------------------------------------------------------------
    # messages — add contact_id FK
    # ------------------------------------------------------------------
    op.add_column("messages", sa.Column("contact_id", UUID(as_uuid=False), sa.ForeignKey("contacts.id"), nullable=True))
    op.create_index("ix_messages_contact_id", "messages", ["contact_id"])

    # ------------------------------------------------------------------
    # replies — add contact_id FK
    # ------------------------------------------------------------------
    op.add_column("replies", sa.Column("contact_id", UUID(as_uuid=False), sa.ForeignKey("contacts.id"), nullable=True))
    op.create_index("ix_replies_contact_id", "replies", ["contact_id"])

    # ------------------------------------------------------------------
    # events — add contact_id FK
    # ------------------------------------------------------------------
    op.add_column("events", sa.Column("contact_id", UUID(as_uuid=False), sa.ForeignKey("contacts.id"), nullable=True))
    op.create_index("ix_events_contact_id", "events", ["contact_id"])


def downgrade() -> None:
    op.drop_index("ix_events_contact_id", table_name="events")
    op.drop_column("events", "contact_id")

    op.drop_index("ix_replies_contact_id", table_name="replies")
    op.drop_column("replies", "contact_id")

    op.drop_index("ix_messages_contact_id", table_name="messages")
    op.drop_column("messages", "contact_id")

    op.drop_table("contacts")

    op.add_column("leads", sa.Column("contact_role", sa.Text, nullable=True))
    op.add_column("leads", sa.Column("contact_phone", sa.Text, nullable=True))
    op.add_column("leads", sa.Column("contact_email", sa.Text, nullable=True))
    op.add_column("leads", sa.Column("discovered_at", TIMESTAMP(timezone=True), nullable=True))
    op.add_column("leads", sa.Column("enriched_data", JSONB, nullable=True))
    op.add_column("leads", sa.Column("source", sa.String(32), nullable=False, server_default="web"))
    op.add_column("leads", sa.Column("url", sa.Text, nullable=False, server_default=""))
    op.add_column("leads", sa.Column("company", sa.Text, nullable=True))
    op.add_column("leads", sa.Column("name", sa.Text, nullable=True))

    op.drop_column("leads", "last_researched_at")
    op.drop_column("leads", "signals")
    op.drop_column("leads", "research_summary")
    op.drop_column("leads", "business_type")
    op.drop_column("leads", "headcount_range")
    op.drop_column("leads", "industry")
    op.drop_column("leads", "domain")
    op.drop_column("leads", "company_name")
    op.drop_index("ix_leads_link_id", table_name="leads")
    op.drop_column("leads", "link_id")

    op.drop_table("links")
