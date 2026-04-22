"""Add customers table, leads.customer_id, and links.identified_at.

Spec: spec/product/07-data-model.md

customers — tenant-wide company knowledge base, cumulative across campaigns.
leads.customer_id — FK linking each campaign lead to the tenant customer record.
links.identified_at — tracks whether a link has been processed by identify_leads.

Revision ID: 0004_customers_and_link_tracking
Revises: 0003_pipeline_restructure
Create Date: 2026-04-25 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

revision: str = "0004_customers_and_link_tracking"
down_revision: str | None = "0003_pipeline_restructure"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # customers table (new)
    # Tenant-wide persistent company record.  Keyed on (tenant_id, domain).
    # The agent appends to research_summary and signals on each run;
    # humans can patch company_name, industry, and notes.
    # ------------------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=False), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("domain", sa.Text, nullable=False),
        sa.Column("company_name", sa.Text, nullable=True),
        sa.Column("industry", sa.Text, nullable=True),
        sa.Column("headcount_range", sa.Text, nullable=True),
        sa.Column("business_type", sa.Text, nullable=True),
        sa.Column("research_summary", sa.Text, nullable=True),
        sa.Column("signals", JSONB, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("first_seen_at", TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_enriched_at", TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_unique_constraint("uq_customers_tenant_domain", "customers", ["tenant_id", "domain"])

    # ------------------------------------------------------------------
    # leads — add customer_id FK
    # ------------------------------------------------------------------
    op.add_column("leads", sa.Column("customer_id", UUID(as_uuid=False), sa.ForeignKey("customers.id"), nullable=True))
    op.create_index("ix_leads_customer_id", "leads", ["customer_id"])

    # ------------------------------------------------------------------
    # links — add identified_at
    # Set by node_identify_leads after processing.  NULL means the link
    # has not yet been run through identify; can be used to retry.
    # ------------------------------------------------------------------
    op.add_column("links", sa.Column("identified_at", TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("links", "identified_at")
    op.drop_index("ix_leads_customer_id", table_name="leads")
    op.drop_column("leads", "customer_id")
    op.drop_constraint("uq_customers_tenant_domain", "customers", type_="unique")
    op.drop_table("customers")
