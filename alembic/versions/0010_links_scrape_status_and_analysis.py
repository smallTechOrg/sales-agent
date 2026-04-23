"""Add scrape_status, page_type, page_summary, page_detail to links.

Spec refs:
  - spec/product/07-data-model.md (links table)
  - spec/product/04-capabilities/02-enrichment.md (link analysis)
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0010_links_scrape_status_and_analysis"
down_revision: str | None = "0009_events_run_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("links", sa.Column("scrape_status", sa.Text, nullable=False, server_default="pending"))
    op.add_column("links", sa.Column("page_type", sa.Text, nullable=True))
    op.add_column("links", sa.Column("page_summary", sa.Text, nullable=True))
    op.add_column("links", sa.Column("page_detail", sa.Text, nullable=True))
    # Fix existing scraped links to have correct status
    op.execute("UPDATE links SET scrape_status = 'scraped' WHERE scraped_at IS NOT NULL AND page_text IS NOT NULL AND page_text != ''")
    op.execute("UPDATE links SET scrape_status = 'failed' WHERE scraped_at IS NOT NULL AND (page_text IS NULL OR page_text = '')")


def downgrade() -> None:
    op.drop_column("links", "page_detail")
    op.drop_column("links", "page_summary")
    op.drop_column("links", "page_type")
    op.drop_column("links", "scrape_status")
