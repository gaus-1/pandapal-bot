"""ensure rest columns exist in users (consecutive_since_rest, rest_offers_count, last_ai_was_rest)

Revision ID: 20260218_rest_cols
Revises: 20260218_erudite
Create Date: 2026-02-18

Добавляет колонки отдыха панды, если их нет (для перерыва на бамбук и видео).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "20260218_rest_cols"
down_revision: Union[str, None] = "20260218_erudite"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS consecutive_since_rest INTEGER NOT NULL DEFAULT 0"
    ))
    conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS rest_offers_count INTEGER NOT NULL DEFAULT 0"
    ))
    conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_ai_was_rest BOOLEAN NOT NULL DEFAULT false"
    ))


def downgrade() -> None:
    # Колонки могли быть добавлены миграцией 20260201_rest — не удаляем
    pass
