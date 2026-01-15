"""add_image_url_to_chat_history

Revision ID: 1cd95f9f0125
Revises: 20260114_add_tetris
Create Date: 2026-01-14 16:26:13.777110

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1cd95f9f0125'
down_revision: Union[str, None] = '20260114_add_tetris'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Безопасное добавление поля image_url - проверяем наличие перед добавлением
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("chat_history")}

    if "image_url" not in columns:
        op.add_column('chat_history', sa.Column('image_url', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('chat_history', 'image_url')
