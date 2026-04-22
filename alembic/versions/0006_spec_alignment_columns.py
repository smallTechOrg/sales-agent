"""Add spec-required DB columns: contacts.seniority_level, contacts.decision_maker_score,
tenants.enabled.

Spec refs:
  - spec/product/07-data-model.md — contacts table: seniority_level TEXT, decision_maker_score NUMERIC
  - spec/product/03-tenancy.md — tenants lifecycle: enabled BOOLEAN
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0006_spec_alignment_columns"
down_revision: str = "0005_cumulative_data_and_run_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # contacts: spec/product/07-data-model.md — seniority_level, decision_maker_score
    op.add_column("contacts", sa.Column("seniority_level", sa.Text(), nullable=True))
    op.add_column("contacts", sa.Column("decision_maker_score", sa.Numeric(), nullable=True))

    # tenants: spec/product/03-tenancy.md — enabled flag for scheduler lifecycle
    op.add_column(
        "tenants",
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("contacts", "seniority_level")
    op.drop_column("contacts", "decision_maker_score")
    op.drop_column("tenants", "enabled")
