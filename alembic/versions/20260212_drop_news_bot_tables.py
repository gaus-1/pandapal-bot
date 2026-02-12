"""drop news bot tables

Revision ID: 20260212_drop_news
Revises: 20260205_emoji
Create Date: 2026-02-12

Удаление таблиц новостного бота: news, news_user_preferences.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260212_drop_news"
down_revision: Union[str, None] = "20260205_emoji"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("news_user_preferences", "news"):
        op.drop_table(table, if_exists=True)


def downgrade() -> None:
    # Восстановление таблиц не реализовано — модели удалены из кода
    pass
