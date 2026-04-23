"""Add website and description columns to companies table.

Spec refs:
  - spec/product/07-data-model.md (companies.website, companies.description)
  - reports/2026-04-23-lead-company-research-concurrency.md
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0011_companies_website_description"
down_revision: str | None = "0009_events_run_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("website", sa.Text, nullable=True))
    op.add_column("companies", sa.Column("description", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "description")
    op.drop_column("companies", "website")
