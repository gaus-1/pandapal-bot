"""Add auto_renew to subscriptions

Добавляет поле auto_renew для автоматического продления подписок:
- auto_renew: включен ли автоплатеж (по умолчанию false)

Revision ID: add_auto_renew
Revises: add_payment_method
Create Date: 2025-01-09 15:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_auto_renew"
down_revision: Union[str, None] = "add_payment_method"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавление поля auto_renew."""
    op.add_column(
        "subscriptions",
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    """Откат изменений."""
    op.drop_column("subscriptions", "auto_renew")
