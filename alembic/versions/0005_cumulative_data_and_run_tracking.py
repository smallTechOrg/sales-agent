"""Cumulative data model: tenant-scoped links, link_leads junction,
contacts customer_id, campaign_runs table.

Spec: spec/product/07-data-model.md

Changes:
- links.campaign_id: drop FK constraint + NOT NULL → nullable (provenance only).
- links unique constraint: replace (tenant_id, campaign_id, url) with (tenant_id, url).
- New table: link_leads — junction mapping links to leads per campaign.
- contacts: add customer_id FK → customers.id (nullable); backfill from leads.
- contacts: add unique constraint (customer_id, email) for cross-campaign dedup.
- New table: campaign_runs — tracks non-blocking agent run lifecycle.

Revision ID: 0005_cumulative_data_and_run_tracking
Revises: 0004_customers_and_link_tracking
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID

revision: str = "0005_cumulative_data_and_run_tracking"
down_revision: str | None = "0004_customers_and_link_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # links — make campaign_id nullable (drop FK + NOT NULL)
    # ------------------------------------------------------------------
    # Drop old FK constraint (name follows Alembic convention)
    op.drop_constraint("links_campaign_id_fkey", "links", type_="foreignkey")
    # Drop old unique index on (tenant_id, campaign_id, url) if it exists
    op.execute("DROP INDEX IF EXISTS idx_links_url")

    op.alter_column("links", "campaign_id", nullable=True)

    # New unique: one URL per tenant (global dedup)
    op.create_unique_constraint("uq_links_tenant_url", "links", ["tenant_id", "url"])

    # ------------------------------------------------------------------
    # link_leads — junction table (link ↔ lead ↔ campaign)
    # ------------------------------------------------------------------
    op.create_table(
        "link_leads",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=False), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("link_id", UUID(as_uuid=False), sa.ForeignKey("links.id"), nullable=False),
        sa.Column("lead_id", UUID(as_uuid=False), sa.ForeignKey("leads.id"), nullable=False),
        sa.Column("campaign_id", UUID(as_uuid=False), sa.ForeignKey("campaigns.id"), nullable=False),
        sa.Column("created_at", TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_unique_constraint("uq_link_leads", "link_leads", ["tenant_id", "link_id", "lead_id"])
    op.create_index("idx_link_leads_link", "link_leads", ["tenant_id", "link_id"])
    op.create_index("idx_link_leads_lead", "link_leads", ["tenant_id", "lead_id"])

    # Backfill link_leads from existing leads rows that have a link_id
    op.execute(
        """
        INSERT INTO link_leads (id, tenant_id, link_id, lead_id, campaign_id, created_at)
        SELECT gen_random_uuid(), l.tenant_id, l.link_id, l.id, l.campaign_id, now()
        FROM leads l
        WHERE l.link_id IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )

    # ------------------------------------------------------------------
    # contacts — add customer_id for cross-campaign dedup
    # ------------------------------------------------------------------
    op.add_column(
        "contacts",
        sa.Column("customer_id", UUID(as_uuid=False), sa.ForeignKey("customers.id"), nullable=True),
    )
    op.create_index("idx_contacts_customer", "contacts", ["tenant_id", "customer_id"])

    # Backfill customer_id from the parent lead's customer_id
    op.execute(
        """
        UPDATE contacts c
        SET customer_id = l.customer_id
        FROM leads l
        WHERE c.lead_id = l.id
          AND l.customer_id IS NOT NULL
        """
    )

    # Cross-campaign unique guard: one contact row per (customer, email)
    op.create_unique_constraint(
        "uq_contacts_customer_email",
        "contacts",
        ["customer_id", "email"],
    )

    # ------------------------------------------------------------------
    # campaign_runs — non-blocking agent run tracking
    # ------------------------------------------------------------------
    op.create_table(
        "campaign_runs",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=False), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("campaign_id", UUID(as_uuid=False), sa.ForeignKey("campaigns.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("current_node", sa.Text, nullable=True),
        sa.Column("started_at", TIMESTAMP(timezone=True), nullable=True),
        sa.Column("finished_at", TIMESTAMP(timezone=True), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_runs_campaign", "campaign_runs", ["tenant_id", "campaign_id"])
    op.create_index(
        "idx_runs_running",
        "campaign_runs",
        ["tenant_id", "campaign_id", "status"],
        postgresql_where=sa.text("status = 'running'"),
    )


def downgrade() -> None:
    op.drop_table("campaign_runs")
    op.drop_constraint("uq_contacts_customer_email", "contacts", type_="unique")
    op.drop_index("idx_contacts_customer", table_name="contacts")
    op.drop_column("contacts", "customer_id")
    op.drop_table("link_leads")
    op.drop_constraint("uq_links_tenant_url", "links", type_="unique")
    op.alter_column("links", "campaign_id", nullable=False)
    op.create_foreign_key("links_campaign_id_fkey", "links", "campaigns", ["campaign_id"], ["id"])
    op.create_index("idx_links_url", "links", ["tenant_id", "campaign_id", "url"], unique=True)
