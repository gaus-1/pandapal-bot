"""Add adaptive learning and homework tables

Добавляет таблицы для адаптивного обучения и проверки ДЗ:
- problem_topics - проблемные темы для повторения
- homework_submissions - проверка домашних заданий

Revision ID: adaptive_homework_2026
Revises: fd7a18529e23
Create Date: 2026-01-20 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "adaptive_homework_2026"
down_revision: Union[str, None] = "fd7a18529e23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Таблица проблемных тем для адаптивного обучения
    op.create_table(
        "problem_topics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("subject", sa.String(length=100), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("error_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("total_attempts", sa.Integer(), server_default="1", nullable=False),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_telegram_id"],
            ["users.telegram_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_telegram_id", "subject", "topic", name="uq_problem_topics_user_subject_topic"),
    )

    # Индексы для problem_topics
    op.create_index(
        "idx_problem_topics_user",
        "problem_topics",
        ["user_telegram_id"],
    )
    op.create_index(
        "idx_problem_topics_subject",
        "problem_topics",
        ["subject"],
    )
    op.create_index(
        "idx_problem_topics_error_count",
        "problem_topics",
        ["error_count"],
    )
    op.create_index(
        "idx_problem_topics_last_error",
        "problem_topics",
        ["last_error_at"],
    )

    # Таблица проверки домашних заданий
    op.create_table(
        "homework_submissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("photo_file_id", sa.String(length=255), nullable=True),
        sa.Column("photo_url", sa.String(length=500), nullable=True),
        sa.Column("subject", sa.String(length=100), nullable=True),
        sa.Column("topic", sa.String(length=255), nullable=True),
        sa.Column("original_text", sa.Text(), nullable=True),
        sa.Column("ai_feedback", sa.Text(), nullable=True),
        sa.Column("has_errors", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("errors_found", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("max_score", sa.Integer(), nullable=True),
        sa.Column(
            "submitted_at",
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

    # Индексы для homework_submissions
    op.create_index(
        "idx_homework_submissions_user",
        "homework_submissions",
        ["user_telegram_id"],
    )
    op.create_index(
        "idx_homework_submissions_subject",
        "homework_submissions",
        ["subject"],
    )
    op.create_index(
        "idx_homework_submissions_submitted",
        "homework_submissions",
        ["submitted_at"],
    )
    op.create_index(
        "idx_homework_submissions_has_errors",
        "homework_submissions",
        ["has_errors"],
    )

    # Добавляем поле difficulty_level в user_progress для адаптивного обучения
    op.add_column(
        "user_progress",
        sa.Column("difficulty_level", sa.Integer(), server_default="1", nullable=True),
    )
    op.add_column(
        "user_progress",
        sa.Column("mastery_score", sa.Float(), server_default="0.0", nullable=True),
    )


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index("idx_homework_submissions_has_errors", table_name="homework_submissions")
    op.drop_index("idx_homework_submissions_submitted", table_name="homework_submissions")
    op.drop_index("idx_homework_submissions_subject", table_name="homework_submissions")
    op.drop_index("idx_homework_submissions_user", table_name="homework_submissions")
    op.drop_index("idx_problem_topics_last_error", table_name="problem_topics")
    op.drop_index("idx_problem_topics_error_count", table_name="problem_topics")
    op.drop_index("idx_problem_topics_subject", table_name="problem_topics")
    op.drop_index("idx_problem_topics_user", table_name="problem_topics")

    # Удаляем таблицы
    op.drop_table("homework_submissions")
    op.drop_table("problem_topics")

    # Удаляем поля из user_progress
    op.drop_column("user_progress", "mastery_score")
    op.drop_column("user_progress", "difficulty_level")
