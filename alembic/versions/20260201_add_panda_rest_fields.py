"""add panda rest offer fields to users

Revision ID: 20260201_rest
Revises: fab52f0ee1f2
Create Date: 2026-02-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260201_rest"
down_revision: Union[str, None] = "fab52f0ee1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("consecutive_since_rest", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("rest_offers_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("last_ai_was_rest", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "last_ai_was_rest")
    op.drop_column("users", "rest_offers_count")
    op.drop_column("users", "consecutive_since_rest")
