"""add_name_mention_fields_to_users

Revision ID: 50775761d394
Revises: a1b2c3d4e5f7
Create Date: 2026-01-08 19:27:49.663428

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "50775761d394"
down_revision: Union[str, None] = "a1b2c3d4e5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поле для отслеживания количества сообщений с последнего обращения по имени
    op.add_column(
        "users",
        sa.Column("last_name_mention_count", sa.Integer(), server_default="0", nullable=False),
    )
    # Добавляем флаг для пропуска запроса имени
    op.add_column(
        "users",
        sa.Column("skip_name_asking", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    # Удаляем добавленные поля
    op.drop_column("users", "skip_name_asking")
    op.drop_column("users", "last_name_mention_count")
