"""
Модели аналитики: метрики (используются для записи бизнес-метрик).

Неиспользуемые таблицы user_sessions, user_events, analytics_reports,
analytics_trends, analytics_alerts, analytics_config удалены миграцией.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class AnalyticsMetric(Base):
    """
    Модель для хранения аналитических метрик.
    Собирает различные показатели производительности и использования.
    """

    __tablename__ = "analytics_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    user_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    __table_args__ = (
        Index("idx_analytics_metrics_name_time", "metric_name", "timestamp"),
        Index("idx_analytics_metrics_user_time", "user_telegram_id", "timestamp"),
        Index("idx_analytics_metrics_period", "period"),
    )

    def __repr__(self) -> str:
        """Строковое представление аналитической метрики"""
        return (
            f"<AnalyticsMetric(id={self.id}, name='{self.metric_name}', "
            f"value={self.metric_value}, type='{self.metric_type}')>"
        )
