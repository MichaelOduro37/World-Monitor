"""Add nasa_eonet and reliefweb to sourcetype enum

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-05 21:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE to add enum values.
    # The IF NOT EXISTS guard makes the migration idempotent.
    op.execute(
        "ALTER TYPE sourcetype ADD VALUE IF NOT EXISTS 'nasa_eonet'"
    )
    op.execute(
        "ALTER TYPE sourcetype ADD VALUE IF NOT EXISTS 'reliefweb'"
    )


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; a full recreate would
    # be needed. For safety, the downgrade is a no-op.
    pass
