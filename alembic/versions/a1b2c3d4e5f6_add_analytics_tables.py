"""Add analytics tables

Добавляет таблицы для системы аналитики:
- analytics_metrics
- user_sessions
- user_events
- analytics_reports
- analytics_trends
- analytics_alerts
- analytics_config

Revision ID: a1b2c3d4e5f6
Revises: 7e511929fac4
Create Date: 2025-01-01 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "7e511929fac4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создание таблиц аналитики."""

    # analytics_metrics
    op.create_table(
        "analytics_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("metric_type", sa.String(length=50), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_analytics_metrics_name_time", "analytics_metrics", ["metric_name", "timestamp"]
    )
    op.create_index(
        "idx_analytics_metrics_user_time", "analytics_metrics", ["user_telegram_id", "timestamp"]
    )
    op.create_index("idx_analytics_metrics_period", "analytics_metrics", ["period"])

    # user_sessions
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "session_start",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("session_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("session_duration", sa.Integer(), nullable=True),
        sa.Column("messages_count", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("ai_interactions", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("voice_messages", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("blocked_messages", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("subjects_covered", sa.JSON(), nullable=True),
        sa.Column("engagement_score", sa.Float(), nullable=True),
        sa.Column("safety_score", sa.Float(), nullable=True),
        sa.Column(
            "session_type", sa.String(length=50), server_default=sa.text("'regular'"), nullable=True
        ),
        sa.Column("device_info", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_user_sessions_user_start", "user_sessions", ["user_telegram_id", "session_start"]
    )
    op.create_index("idx_user_sessions_duration", "user_sessions", ["session_duration"])
    op.create_index("idx_user_sessions_type", "user_sessions", ["session_type"])

    # user_events
    op.create_table(
        "user_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("event_data", sa.JSON(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column(
            "importance", sa.String(length=20), server_default=sa.text("'normal'"), nullable=True
        ),
        sa.Column("processed", sa.Boolean(), server_default=sa.text("FALSE"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_user_events_user_time", "user_events", ["user_telegram_id", "timestamp"])
    op.create_index("idx_user_events_type", "user_events", ["event_type"])
    op.create_index("idx_user_events_importance", "user_events", ["importance"])
    op.create_index("idx_user_events_processed", "user_events", ["processed"])

    # analytics_reports
    op.create_table(
        "analytics_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("report_period", sa.String(length=20), nullable=False),
        sa.Column("report_data", sa.JSON(), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("generated_by", sa.String(length=100), nullable=True),
        sa.Column("parent_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("child_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("is_scheduled", sa.Boolean(), server_default=sa.text("FALSE"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_analytics_reports_type_period", "analytics_reports", ["report_type", "report_period"]
    )
    op.create_index("idx_analytics_reports_parent", "analytics_reports", ["parent_telegram_id"])
    op.create_index("idx_analytics_reports_generated", "analytics_reports", ["generated_at"])

    # analytics_trends
    op.create_table(
        "analytics_trends",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("trend_direction", sa.String(length=20), nullable=False),
        sa.Column("trend_strength", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("prediction_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_analytics_trends_metric", "analytics_trends", ["metric_name"])
    op.create_index(
        "idx_analytics_trends_period", "analytics_trends", ["period_start", "period_end"]
    )
    op.create_index("idx_analytics_trends_confidence", "analytics_trends", ["confidence"])

    # analytics_alerts
    op.create_table(
        "analytics_alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column("alert_level", sa.String(length=20), nullable=False),
        sa.Column("alert_message", sa.Text(), nullable=False),
        sa.Column("alert_data", sa.JSON(), nullable=True),
        sa.Column(
            "triggered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(length=100), nullable=True),
        sa.Column("parent_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("child_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("is_sent", sa.Boolean(), server_default=sa.text("FALSE"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_analytics_alerts_type_level", "analytics_alerts", ["alert_type", "alert_level"]
    )
    op.create_index("idx_analytics_alerts_parent", "analytics_alerts", ["parent_telegram_id"])
    op.create_index("idx_analytics_alerts_triggered", "analytics_alerts", ["triggered_at"])
    op.create_index("idx_analytics_alerts_resolved", "analytics_alerts", ["resolved_at"])

    # analytics_config
    op.create_table(
        "analytics_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("config_key", sa.String(length=100), nullable=False),
        sa.Column("config_value", sa.JSON(), nullable=False),
        sa.Column("config_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_analytics_config_key", "analytics_config", ["config_key"])
    op.create_index("uq_analytics_config_key", "analytics_config", ["config_key"], unique=True)


def downgrade() -> None:
    """Удаление таблиц аналитики."""
    op.drop_table("analytics_config")
    op.drop_table("analytics_alerts")
    op.drop_table("analytics_trends")
    op.drop_table("analytics_reports")
    op.drop_table("user_events")
    op.drop_table("user_sessions")
    op.drop_table("analytics_metrics")
