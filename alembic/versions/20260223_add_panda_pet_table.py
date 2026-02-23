"""add panda_pet table for My Panda tamagotchi

Revision ID: 20260223_panda
Revises: 20260220_referrer_8198136020
Create Date: 2026-02-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260223_panda"
down_revision: Union[str, None] = "20260220_referrer_8198136020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Убираем старую таблицу, если осталась от 20260204 (до drop 20260218), чтобы не было дубля и ошибки "already exists"
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute(sa.text("DROP TABLE IF EXISTS panda_pet CASCADE"))
    else:
        op.execute(sa.text("DROP TABLE IF EXISTS panda_pet"))
    op.create_table(
        "panda_pet",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column(
            "user_telegram_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column("hunger", sa.SmallInteger(), nullable=False, server_default="60"),
        sa.Column("mood", sa.SmallInteger(), nullable=False, server_default="70"),
        sa.Column("energy", sa.SmallInteger(), nullable=False, server_default="50"),
        sa.Column("last_fed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_played_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_slept_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "feed_count_since_hour_start",
            sa.SmallInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("feed_hour_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "total_fed_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_played_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "consecutive_visit_days",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("last_visit_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("achievements", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_telegram_id"],
            ["users.telegram_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_panda_pet_user", "panda_pet", ["user_telegram_id"], unique=False)
    op.create_unique_constraint(
        "uq_panda_pet_user_telegram_id", "panda_pet", ["user_telegram_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_panda_pet_user_telegram_id", "panda_pet", type_="unique")
    op.drop_index("idx_panda_pet_user", table_name="panda_pet")
    op.drop_table("panda_pet")
