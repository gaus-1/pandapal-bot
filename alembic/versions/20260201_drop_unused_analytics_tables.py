"""drop unused analytics tables

Revision ID: 20260201_drop_analytics
Revises: 20260201_rest
Create Date: 2026-02-01

Удаление неиспользуемых таблиц: user_sessions, user_events,
analytics_reports, analytics_trends, analytics_alerts, analytics_config.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260201_drop_analytics"
down_revision: Union[str, None] = "20260201_merge"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in (
        "analytics_alerts",
        "analytics_config",
        "analytics_reports",
        "analytics_trends",
        "user_events",
        "user_sessions",
    ):
        op.drop_table(table, if_exists=True)


def downgrade() -> None:
    # Восстановление таблиц не реализовано — модели удалены из кода
    pass
