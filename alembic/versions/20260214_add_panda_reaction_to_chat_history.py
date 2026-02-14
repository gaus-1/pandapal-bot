"""add panda_reaction to chat_history

Revision ID: 20260214_panda_reaction
Revises: 20260212_knowledge_vec
Create Date: 2026-02-14

Колонка panda_reaction для сохранения реакции панды на фидбек (happy, eating, offended, questioning).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260214_panda_reaction"
down_revision: Union[str, None] = "20260212_knowledge_vec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_history",
        sa.Column("panda_reaction", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("chat_history", "panda_reaction")
