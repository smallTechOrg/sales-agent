"""Add run_id to events for per-run aggregation.

Spec refs:
  - spec/product/07-data-model.md (events table)
  - spec/product/09-api.md (run summary endpoint)
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0009_events_run_id"
down_revision: str | None = "0008_cost_tracking_and_page_excerpt"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("events", sa.Column("run_id", sa.Text, nullable=True, index=True))


def downgrade() -> None:
    op.drop_column("events", "run_id")
