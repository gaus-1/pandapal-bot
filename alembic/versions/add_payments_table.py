"""Add payments table

Создает таблицу payments для хранения полной истории всех платежей
(успешных и неуспешных) для аудита, аналитики и отладки.

Revision ID: add_payments_table
Revises: add_payment_method
Create Date: 2025-01-04 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_payments_table"
down_revision: Union[str, None] = "add_payment_method"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создание таблицы payments."""

    # Создаем таблицу payments
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "payment_id",
            sa.String(length=255),
            nullable=False,
        ),  # Уникальный ID от ЮKassa или Telegram
        sa.Column(
            "user_telegram_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            sa.Integer(),
            nullable=True,
        ),  # Связь с подпиской (если платеж успешен)
        sa.Column(
            "payment_method",
            sa.String(length=20),
            nullable=False,
        ),  # 'stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other'
        sa.Column("plan_id", sa.String(length=20), nullable=False),  # 'month', 'year'
        sa.Column("amount", sa.Float(), nullable=False),  # Сумма платежа
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="RUB"),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),  # 'pending', 'succeeded', 'cancelled', 'failed'
        sa.Column("payment_metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("webhook_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_telegram_id"],
            ["users.telegram_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["subscriptions.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Создаем уникальный индекс на payment_id
    op.create_index(
        "idx_payments_payment_id",
        "payments",
        ["payment_id"],
        unique=True,
    )

    # Создаем индексы для быстрого поиска
    op.create_index(
        "idx_payments_user_telegram_id",
        "payments",
        ["user_telegram_id"],
    )
    op.create_index(
        "idx_payments_subscription_id",
        "payments",
        ["subscription_id"],
    )
    op.create_index(
        "idx_payments_status",
        "payments",
        ["status"],
    )
    op.create_index(
        "idx_payments_user_status",
        "payments",
        ["user_telegram_id", "status"],
    )
    op.create_index(
        "idx_payments_created",
        "payments",
        ["created_at"],
    )
    op.create_index(
        "idx_payments_paid",
        "payments",
        ["paid_at"],
    )

    # Добавляем constraints
    op.create_check_constraint(
        "ck_payments_payment_method",
        "payments",
        "payment_method IN ('stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other')",
    )
    op.create_check_constraint(
        "ck_payments_plan_id",
        "payments",
        "plan_id IN ('month', 'year')",
    )
    op.create_check_constraint(
        "ck_payments_status",
        "payments",
        "status IN ('pending', 'succeeded', 'cancelled', 'failed')",
    )


def downgrade() -> None:
    """Откат изменений."""

    # Удаляем constraints
    op.drop_constraint("ck_payments_status", "payments", type_="check")
    op.drop_constraint("ck_payments_plan_id", "payments", type_="check")
    op.drop_constraint("ck_payments_payment_method", "payments", type_="check")

    # Удаляем индексы
    op.drop_index("idx_payments_paid", table_name="payments")
    op.drop_index("idx_payments_created", table_name="payments")
    op.drop_index("idx_payments_user_status", table_name="payments")
    op.drop_index("idx_payments_status", table_name="payments")
    op.drop_index("idx_payments_subscription_id", table_name="payments")
    op.drop_index("idx_payments_user_telegram_id", table_name="payments")
    op.drop_index("idx_payments_payment_id", table_name="payments")

    # Удаляем таблицу
    op.drop_table("payments")
