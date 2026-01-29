"""add user activity fields

Revision ID: 20260105_activity
Revises: add_payments_table
Create Date: 2026-01-05

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260105_activity"
down_revision: Union[str, None] = "add_payments_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поля активности и напоминаний в таблицу users
    op.add_column(
        "users", sa.Column("message_count", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column("users", sa.Column("last_activity", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Удаляем добавленные поля
    op.drop_column("users", "reminder_sent_at")
    op.drop_column("users", "last_activity")
    op.drop_column("users", "message_count")
