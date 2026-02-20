"""Add referrer 8198136020

Добавляет в whitelist рефереров telegram_id=8198136020.

Revision ID: 20260220_referrer_8198136020
Revises: 20260218_rest_cols
Create Date: 2026-02-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260220_referrer_8198136020"
down_revision: Union[str, None] = "20260218_rest_cols"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Исторически первый реферер был вставлен с явным id=1.
    # На чистых БД sequence может остаться на старте и вернуть снова 1.
    # Синхронизируем sequence с фактическим MAX(id), чтобы избежать PK-конфликта.
    op.execute(
        sa.text(
            """
            SELECT setval(
                pg_get_serial_sequence('referrers', 'id'),
                COALESCE((SELECT MAX(id) FROM referrers), 1),
                true
            )
            """
        )
    )

    op.execute(
        sa.text(
            """
            INSERT INTO referrers (telegram_id, comment, created_at)
            SELECT :telegram_id, :comment, CURRENT_TIMESTAMP
            WHERE NOT EXISTS (
                SELECT 1 FROM referrers WHERE telegram_id = :telegram_id
            )
            """
        ).bindparams(
            telegram_id=8198136020,
            comment="Партнёр",
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM referrers WHERE telegram_id = :telegram_id").bindparams(
            telegram_id=8198136020
        )
    )
