"""add last_climb_at, last_fall_at to panda_pet (1 hour cooldown each)

Revision ID: 20260223_climb_fall
Revises: 20260223_toilet
Create Date: 2026-02-23

На дерево и Упасть с дерева — раз в час.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260223_climb_fall"
down_revision: Union[str, None] = "20260223_toilet"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "panda_pet",
        sa.Column("last_climb_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "panda_pet",
        sa.Column("last_fall_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("panda_pet", "last_fall_at")
    op.drop_column("panda_pet", "last_climb_at")
