"""Add premium subscriptions

Добавляет поддержку Premium подписок:
- Поле premium_until в таблице users
- Таблица subscriptions для хранения подписок

Revision ID: add_premium_subs
Revises: a1b2c3d4e5f6
Create Date: 2025-01-15 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_premium_subs"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавление поддержки Premium подписок."""

    # Добавляем поле premium_until в таблицу users
    op.add_column(
        "users",
        sa.Column("premium_until", sa.DateTime(timezone=True), nullable=True),
    )

    # Создаем таблицу subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("plan_id", sa.String(length=20), nullable=False),
        sa.Column(
            "starts_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("transaction_id", sa.String(length=255), nullable=True),
        sa.Column("invoice_payload", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_telegram_id"],
            ["users.telegram_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("plan_id IN ('week', 'month', 'year')", name="ck_subscriptions_plan_id"),
    )

    # Создаем индексы
    op.create_index(
        "idx_subscriptions_user_active",
        "subscriptions",
        ["user_telegram_id", "is_active"],
    )
    op.create_index("idx_subscriptions_expires", "subscriptions", ["expires_at"])


def downgrade() -> None:
    """Откат изменений."""

    # Удаляем индексы
    op.drop_index("idx_subscriptions_expires", table_name="subscriptions")
    op.drop_index("idx_subscriptions_user_active", table_name="subscriptions")

    # Удаляем таблицу subscriptions
    op.drop_table("subscriptions")

    # Удаляем поле premium_until из users
    op.drop_column("users", "premium_until")
