"""Add page_excerpt to links and cost/token columns to campaign_runs.

Spec refs:
  - spec/product/07-data-model.md (links.page_excerpt, campaign_runs cost columns)
  - spec/product/09-api.md (link object shape, campaign-run object shape)
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0008_cost_tracking_and_page_excerpt"
down_revision: str | None = "0007_rename_customers_contacts_to_companies_people"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("links", sa.Column("page_excerpt", sa.Text, nullable=True))

    op.add_column("campaign_runs", sa.Column("input_tokens", sa.Integer, nullable=False, server_default="0"))
    op.add_column("campaign_runs", sa.Column("output_tokens", sa.Integer, nullable=False, server_default="0"))
    op.add_column("campaign_runs", sa.Column("total_tokens", sa.Integer, nullable=False, server_default="0"))
    op.add_column("campaign_runs", sa.Column("llm_call_count", sa.Integer, nullable=False, server_default="0"))
    op.add_column("campaign_runs", sa.Column("estimated_cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("campaign_runs", "estimated_cost_usd")
    op.drop_column("campaign_runs", "llm_call_count")
    op.drop_column("campaign_runs", "total_tokens")
    op.drop_column("campaign_runs", "output_tokens")
    op.drop_column("campaign_runs", "input_tokens")
    op.drop_column("links", "page_excerpt")
