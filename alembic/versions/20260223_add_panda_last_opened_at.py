"""add last_opened_at to panda_pet for 24h absence offended

Revision ID: 20260223_opened
Revises: 20260223_panda
Create Date: 2026-02-23

Если пользователь не заходил в тамагочи 24 часа, при следующем заходе показывается обиженная панда (mood 65).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260223_opened"
down_revision: Union[str, None] = "20260223_panda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "panda_pet",
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("panda_pet", "last_opened_at")
