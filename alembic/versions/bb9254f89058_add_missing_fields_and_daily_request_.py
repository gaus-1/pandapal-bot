"""add missing fields and daily_request_counts table

Revision ID: bb9254f89058
Revises: d4337e0b268f
Create Date: 2026-01-10 20:09:19.469025

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bb9254f89058"
down_revision: Union[str, None] = "d4337e0b268f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавление недостающих полей и таблицы daily_request_counts."""
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)

    # Проверяем и добавляем поля в users
    users_columns = {col["name"] for col in inspector.get_columns("users")}

    if "last_name_mention_count" not in users_columns:
        op.add_column(
            "users",
            sa.Column("last_name_mention_count", sa.Integer(), server_default="0", nullable=False),
        )

    if "skip_name_asking" not in users_columns:
        op.add_column(
            "users",
            sa.Column("skip_name_asking", sa.Boolean(), server_default="false", nullable=False),
        )

    if "non_educational_questions_count" not in users_columns:
        op.add_column(
            "users",
            sa.Column(
                "non_educational_questions_count", sa.Integer(), server_default="0", nullable=False
            ),
        )

    # Проверяем и добавляем поля в subscriptions
    subscriptions_columns = {col["name"] for col in inspector.get_columns("subscriptions")}

    if "auto_renew" not in subscriptions_columns:
        op.add_column(
            "subscriptions",
            sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default="false"),
        )

    if "saved_payment_method_id" not in subscriptions_columns:
        op.add_column(
            "subscriptions",
            sa.Column("saved_payment_method_id", sa.String(length=255), nullable=True),
        )

    # Создаем таблицу daily_request_counts, если её нет
    existing_tables = inspector.get_table_names()
    if "daily_request_counts" not in existing_tables:
        op.create_table(
            "daily_request_counts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
            sa.Column("date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "last_request_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.ForeignKeyConstraint(
                ["user_telegram_id"],
                ["users.telegram_id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "idx_daily_request_user_date",
            "daily_request_counts",
            ["user_telegram_id", "date"],
            unique=True,
        )
        op.create_index(
            "idx_daily_request_date",
            "daily_request_counts",
            ["date"],
            unique=False,
        )


def downgrade() -> None:
    """Откат изменений."""
    # Удаляем таблицу daily_request_counts
    op.drop_index("idx_daily_request_date", table_name="daily_request_counts")
    op.drop_index("idx_daily_request_user_date", table_name="daily_request_counts")
    op.drop_table("daily_request_counts")

    # Удаляем поля из subscriptions
    op.drop_column("subscriptions", "saved_payment_method_id")
    op.drop_column("subscriptions", "auto_renew")

    # Удаляем поля из users
    op.drop_column("users", "non_educational_questions_count")
    op.drop_column("users", "skip_name_asking")
    op.drop_column("users", "last_name_mention_count")
