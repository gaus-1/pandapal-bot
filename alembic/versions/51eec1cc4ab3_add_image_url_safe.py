"""add_image_url_safe

Revision ID: 51eec1cc4ab3
Revises: a1b2c3d4e5f8
Create Date: 2026-01-14 16:57:08.899435

"""
from typing import Sequence, Union

from alembic import op
from loguru import logger
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51eec1cc4ab3'
down_revision: Union[str, None] = 'a1b2c3d4e5f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Безопасное добавление поля image_url - проверяем наличие перед добавлением
    from sqlalchemy import inspect, text

    conn = op.get_bind()
    inspector = inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("chat_history")}

    if "image_url" not in columns:
        op.add_column('chat_history', sa.Column('image_url', sa.Text(), nullable=True))
        logger.info("✅ Поле image_url добавлено в chat_history")
    else:
        logger.info("ℹ️ Поле image_url уже существует в chat_history, пропускаем")


def downgrade() -> None:
    # Безопасное удаление поля - проверяем наличие перед удалением
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("chat_history")}

    if "image_url" in columns:
        op.drop_column('chat_history', 'image_url')
        logger.info("✅ Поле image_url удалено из chat_history")
    else:
        logger.info("ℹ️ Поле image_url не существует в chat_history, пропускаем")
