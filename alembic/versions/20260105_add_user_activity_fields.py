"""add user activity fields

Revision ID: 20260105_activity
Revises: add_payments_table
Create Date: 2026-01-05

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260105_activity"
down_revision = "add_payments_table"
branch_labels = None
depends_on = None


def upgrade():
    # Добавляем поля активности и напоминаний в таблицу users
    op.add_column(
        "users", sa.Column("message_count", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column("users", sa.Column("last_activity", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    # Удаляем добавленные поля
    op.drop_column("users", "reminder_sent_at")
    op.drop_column("users", "last_activity")
    op.drop_column("users", "message_count")
