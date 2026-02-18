"""add bamboo_break fields to users and video_url to chat_history

Revision ID: 20260218_bamboo
Revises: 20260218_drop_panda
Create Date: 2026-02-18

Суточный лимит показов видео перерыва на бамбук (3 в день); video_url в истории чата.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260218_bamboo"
down_revision: Union[str, None] = "20260218_drop_panda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("bamboo_break_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("bamboo_breaks_today", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "chat_history",
        sa.Column("video_url", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("chat_history", "video_url")
    op.drop_column("users", "bamboo_breaks_today")
    op.drop_column("users", "bamboo_break_date")
