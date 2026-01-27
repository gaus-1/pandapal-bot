"""add_news_user_preferences_table

Создает таблицу news_user_preferences для хранения предпочтений пользователей новостного бота.

Revision ID: 42ccec998518
Revises: 76c9942db20e
Create Date: 2026-01-27 17:10:07.587012

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "42ccec998518"
down_revision: Union[str, None] = "76c9942db20e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создание таблицы news_user_preferences."""
    op.create_table(
        "news_user_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("grade", sa.Integer(), nullable=True),
        sa.Column("categories", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("read_news_ids", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "daily_notifications",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Индексы
    op.create_index("idx_news_prefs_user", "news_user_preferences", ["user_telegram_id"], unique=True)


def downgrade() -> None:
    """Откат изменений."""
    op.drop_index("idx_news_prefs_user", table_name="news_user_preferences")
    op.drop_table("news_user_preferences")
