"""Add saved_payment_method_id to subscriptions

Добавляет поле saved_payment_method_id для хранения ID сохраненного метода оплаты
в ЮKassa для автоплатежей.

Revision ID: add_saved_payment_method_id
Revises: add_auto_renew
Create Date: 2025-01-09 16:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_saved_payment_method_id"
down_revision: Union[str, None] = "add_auto_renew"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавление поля saved_payment_method_id."""
    op.add_column(
        "subscriptions",
        sa.Column("saved_payment_method_id", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    """Откат изменений."""
    op.drop_column("subscriptions", "saved_payment_method_id")
