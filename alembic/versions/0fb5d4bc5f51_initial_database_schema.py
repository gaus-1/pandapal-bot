"""Initial database schema

Revision ID: 0fb5d4bc5f51
Revises:
Create Date: 2025-10-02 19:04:05.763728

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0fb5d4bc5f51"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("grade", sa.Integer(), nullable=True),
        sa.Column("user_type", sa.String(length=20), nullable=True),
        sa.Column("parent_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_telegram_id"],
            ["users.telegram_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )

    # Create learning_sessions table
    op.create_table(
        "learning_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("subject", sa.String(length=100), nullable=True),
        sa.Column("topic", sa.String(length=255), nullable=True),
        sa.Column("difficulty_level", sa.Integer(), nullable=True),
        sa.Column("questions_answered", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("correct_answers", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column(
            "session_start",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("session_end", sa.TIMESTAMP(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), server_default=sa.text("FALSE"), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_telegram_id"],
            ["users.telegram_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create user_progress table
    op.create_table(
        "user_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("subject", sa.String(length=100), nullable=True),
        sa.Column("level", sa.Integer(), nullable=True),
        sa.Column("points", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("achievements", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "last_activity",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_telegram_id"],
            ["users.telegram_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create chat_history table
    op.create_table(
        "chat_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("message_text", sa.Text(), nullable=True),
        sa.Column("message_type", sa.String(length=50), nullable=True),
        sa.Column(
            "timestamp", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["user_telegram_id"],
            ["users.telegram_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("chat_history")
    op.drop_table("user_progress")
    op.drop_table("learning_sessions")
    op.drop_table("users")
