"""Merge branches: links_scrape_status_and_analysis + companies_website_description

Revision ID: 98cea20f65f2
Revises: 0010_links_scrape_status_and_analysis, 0011_companies_website_description
Create Date: 2026-04-23 15:28:06.486495
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '98cea20f65f2'
down_revision: Union[str, None] = ('0010_links_scrape_status_and_analysis', '0011_companies_website_description')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
