"""Add referral tables and users.referrer_telegram_id

Реферальная программа: referrers (whitelist), users.referrer_telegram_id,
referral_payouts (начисления). Первый реферер: 729414271.

Revision ID: 20260210_referral
Revises: 20260203_gender
Create Date: 2026-02-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260210_referral"
down_revision: Union[str, None] = "20260203_gender"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "referrers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("comment", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_referrers_telegram_id", "referrers", ["telegram_id"], unique=True)

    op.add_column(
        "users",
        sa.Column("referrer_telegram_id", sa.BigInteger(), nullable=True),
    )
    op.create_index("idx_users_referrer_telegram_id", "users", ["referrer_telegram_id"])

    op.create_table(
        "referral_payouts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("referrer_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("payment_id", sa.String(length=255), nullable=False),
        sa.Column("amount_rub", sa.Float(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
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
    )
    op.create_index(
        "idx_referral_payouts_payment_id",
        "referral_payouts",
        ["payment_id"],
        unique=True,
    )
    op.create_index(
        "idx_referral_payouts_referrer_telegram_id",
        "referral_payouts",
        ["referrer_telegram_id"],
    )
    op.create_index(
        "idx_referral_payouts_referrer_paid",
        "referral_payouts",
        ["referrer_telegram_id", "paid_at"],
    )

    op.execute(
        sa.text(
            "INSERT INTO referrers (id, telegram_id, comment, created_at) "
            "VALUES (1, 729414271, 'Преподаватель', CURRENT_TIMESTAMP)"
        )
    )


def downgrade() -> None:
    op.drop_index("idx_referral_payouts_referrer_paid", table_name="referral_payouts")
    op.drop_index("idx_referral_payouts_referrer_telegram_id", table_name="referral_payouts")
    op.drop_index("idx_referral_payouts_payment_id", table_name="referral_payouts")
    op.drop_table("referral_payouts")
    op.drop_index("idx_users_referrer_telegram_id", table_name="users")
    op.drop_column("users", "referrer_telegram_id")
    op.drop_index("idx_referrers_telegram_id", table_name="referrers")
    op.drop_table("referrers")
