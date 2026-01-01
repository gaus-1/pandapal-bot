"""
Сервис для записи бизнес-метрик в базу данных
Собирает метрики безопасности, образовательной эффективности и технические показатели

Все метрики записываются в таблицу analytics_metrics для последующего анализа
"""

from datetime import datetime
from typing import Dict, Optional

from loguru import logger
from sqlalchemy.orm import Session

from bot.models import AnalyticsMetric


class AnalyticsService:
    """
    Сервис для записи бизнес-метрик
    Использует существующую модель AnalyticsMetric
    """

    def __init__(self, db: Session):
        """
        Инициализация сервиса аналитики

        Args:
            db: Сессия SQLAlchemy
        """
        self.db = db

    def record_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_type: str,
        period: str = "day",
        user_telegram_id: Optional[int] = None,
        tags: Optional[Dict] = None,
    ) -> AnalyticsMetric:
        """
        Записать метрику в базу данных

        Args:
            metric_name: Название метрики (например, "blocked_messages_count")
            metric_value: Значение метрики
            metric_type: Тип метрики (safety, education, parent, technical)
            period: Период агрегации (minute, hour, day, week, month)
            user_telegram_id: ID пользователя (опционально)
            tags: Дополнительные теги для фильтрации (опционально)

        Returns:
            AnalyticsMetric: Созданная запись метрики
        """
        try:
            metric = AnalyticsMetric(
                metric_name=metric_name,
                metric_value=metric_value,
                metric_type=metric_type,
                period=period,
                user_telegram_id=user_telegram_id,
                tags=tags or {},
                timestamp=datetime.now(),
            )
            self.db.add(metric)
            self.db.flush()
            return metric
        except Exception as e:
            logger.error(f"❌ Ошибка записи метрики {metric_name}: {e}")
            raise

    def record_safety_metric(
        self,
        metric_name: str,
        value: float,
        user_telegram_id: Optional[int] = None,
        category: Optional[str] = None,
    ) -> None:
        """
        Записать метрику безопасности

        Args:
            metric_name: Название метрики (blocked_messages, safety_index, etc.)
            value: Значение метрики
            user_telegram_id: ID пользователя (опционально)
            category: Категория блокировки (опционально)
        """
        try:
            tags = {}
            if category:
                tags["category"] = category

            self.record_metric(
                metric_name=metric_name,
                metric_value=value,
                metric_type="safety",
                user_telegram_id=user_telegram_id,
                tags=tags,
            )
        except Exception as e:
            logger.error(f"❌ Ошибка записи метрики безопасности: {e}")

    def record_education_metric(
        self,
        metric_name: str,
        value: float,
        user_telegram_id: Optional[int] = None,
        subject: Optional[str] = None,
    ) -> None:
        """
        Записать метрику образовательной эффективности

        Args:
            metric_name: Название метрики (messages_per_child, session_duration, etc.)
            value: Значение метрики
            user_telegram_id: ID пользователя (опционально)
            subject: Предмет (опционально)
        """
        try:
            tags = {}
            if subject:
                tags["subject"] = subject

            self.record_metric(
                metric_name=metric_name,
                metric_value=value,
                metric_type="education",
                user_telegram_id=user_telegram_id,
                tags=tags,
            )
        except Exception as e:
            logger.error(f"❌ Ошибка записи метрики образования: {e}")

    def record_parent_metric(
        self,
        metric_name: str,
        value: float,
        parent_telegram_id: Optional[int] = None,
    ) -> None:
        """
        Записать метрику родительского контроля

        Args:
            metric_name: Название метрики (dashboard_views, children_count, etc.)
            value: Значение метрики
            parent_telegram_id: ID родителя (опционально)
        """
        try:
            self.record_metric(
                metric_name=metric_name,
                metric_value=value,
                metric_type="parent",
                user_telegram_id=parent_telegram_id,
            )
        except Exception as e:
            logger.error(f"❌ Ошибка записи метрики родителя: {e}")

    def record_technical_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict] = None,
    ) -> None:
        """
        Записать техническую метрику

        Args:
            metric_name: Название метрики (ai_response_time, error_count, etc.)
            value: Значение метрики
            tags: Дополнительные теги (опционально)
        """
        try:
            self.record_metric(
                metric_name=metric_name,
                metric_value=value,
                metric_type="technical",
                tags=tags or {},
            )
        except Exception as e:
            logger.error(f"❌ Ошибка записи технической метрики: {e}")
