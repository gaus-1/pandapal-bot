"""add_panda_lazy_until_field

Revision ID: a1b2c3d4e5f8
Revises: 6e97d652b9a0
Create Date: 2026-01-13 16:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f8"
down_revision: Union[str, None] = "6e97d652b9a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поле для отслеживания времени, когда панда снова станет активной после "ленивости"
    op.add_column(
        "users",
        sa.Column(
            "panda_lazy_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # Удаляем добавленное поле
    op.drop_column("users", "panda_lazy_until")
