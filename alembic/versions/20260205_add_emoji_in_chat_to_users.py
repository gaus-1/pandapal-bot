"""add emoji_in_chat preference to users

Revision ID: 20260205_emoji
Revises: 20260204_panda
Create Date: 2026-02-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260205_emoji"
down_revision: Union[str, None] = "20260204_panda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("emoji_in_chat", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "emoji_in_chat")
