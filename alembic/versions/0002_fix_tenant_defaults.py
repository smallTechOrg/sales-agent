"""Fix tenant table server defaults to match spec/product/07-data-model.md.

retargeting_cooldown_days: 90 → 30
default_approval_mode: 'approve_all' → 'full_auto'

Revision ID: 0002_fix_tenant_defaults
Revises: 0001_initial
Create Date: 2026-04-21 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_fix_tenant_defaults"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "tenants",
        "retargeting_cooldown_days",
        server_default="30",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "tenants",
        "default_approval_mode",
        server_default="full_auto",
        existing_type=sa.String(64),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "tenants",
        "retargeting_cooldown_days",
        server_default="90",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "tenants",
        "default_approval_mode",
        server_default="approve_all",
        existing_type=sa.String(64),
        existing_nullable=False,
    )
