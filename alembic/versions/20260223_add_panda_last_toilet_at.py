"""add last_toilet_at to panda_pet for toilet action (20 min cooldown)

Revision ID: 20260223_toilet
Revises: 20260223_opened
Create Date: 2026-02-23

Кнопка «Хочет в туалет» — кулдаун 20 минут, после нажатия 10 сек показ довольной панды.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260223_toilet"
down_revision: Union[str, None] = "20260223_opened"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "panda_pet",
        sa.Column("last_toilet_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("panda_pet", "last_toilet_at")
