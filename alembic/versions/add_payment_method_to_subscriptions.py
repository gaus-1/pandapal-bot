"""Add payment method to subscriptions

Добавляет поля для хранения информации о способе оплаты:
- payment_method: способ оплаты (stars, yookassa_card, yookassa_sbp, yookassa_other)
- payment_id: ID платежа в платежной системе
- Индекс на payment_id для быстрого поиска

Revision ID: add_payment_method
Revises: add_premium_subs
Create Date: 2025-01-18 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_payment_method"
down_revision: Union[str, None] = "add_premium_subs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавление полей для способа оплаты."""

    # Добавляем поле payment_method
    op.add_column(
        "subscriptions",
        sa.Column("payment_method", sa.String(length=20), nullable=True),
    )

    # Добавляем поле payment_id
    op.add_column(
        "subscriptions",
        sa.Column("payment_id", sa.String(length=255), nullable=True),
    )

    # Создаем индекс на payment_id для быстрого поиска
    op.create_index(
        "idx_subscriptions_payment_id",
        "subscriptions",
        ["payment_id"],
    )

    # Добавляем constraint для payment_method
    op.create_check_constraint(
        "ck_subscriptions_payment_method",
        "subscriptions",
        "payment_method IS NULL OR payment_method IN ('stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other')",
    )


def downgrade() -> None:
    """Откат изменений."""

    # Удаляем constraint
    op.drop_constraint("ck_subscriptions_payment_method", "subscriptions", type_="check")

    # Удаляем индекс
    op.drop_index("idx_subscriptions_payment_id", table_name="subscriptions")

    # Удаляем колонки
    op.drop_column("subscriptions", "payment_id")
    op.drop_column("subscriptions", "payment_method")
