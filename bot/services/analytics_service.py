"""
Сервис для записи бизнес-метрик в базу данных
Собирает метрики безопасности, образовательной эффективности и технические показатели

Все метрики записываются в таблицу analytics_metrics для последующего анализа
"""

from datetime import UTC, datetime

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
        user_telegram_id: int | None = None,
        tags: dict | None = None,
    ) -> AnalyticsMetric:
        """
        Записать метрику в базу данных

        Args:
            metric_name: Название метрики (например, "blocked_messages_count")
            metric_value: Значение метрики
            metric_type: Тип метрики (safety, education, technical)
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
        user_telegram_id: int | None = None,
        category: str | None = None,
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
        user_telegram_id: int | None = None,
        subject: str | None = None,
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

    def record_technical_metric(
        self,
        metric_name: str,
        value: float,
        tags: dict | None = None,
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

    def get_messages_per_day(self, telegram_id: int, days: int = 7) -> dict:
        """
        Получить статистику сообщений по дням (детальная аналитика для Premium).

        Args:
            telegram_id: Telegram ID пользователя
            days: Количество дней для анализа

        Returns:
            Dict: Статистика по дням
        """
        from datetime import datetime, timedelta

        from sqlalchemy import func, select

        from bot.models import ChatHistory

        now = datetime.now(UTC)
        start_date = now - timedelta(days=days)

        # Подсчет сообщений по дням
        stmt = (
            select(
                func.date(ChatHistory.timestamp).label("date"),
                func.count(ChatHistory.id).label("count"),
            )
            .where(ChatHistory.user_telegram_id == telegram_id)
            .where(ChatHistory.timestamp >= start_date)
            .group_by(func.date(ChatHistory.timestamp))
            .order_by(func.date(ChatHistory.timestamp))
        )

        results = self.db.execute(stmt).all()
        messages_per_day = {str(row.date): row.count for row in results}

        return {
            "period_days": days,
            "messages_per_day": messages_per_day,
            "total_messages": sum(messages_per_day.values()),
        }

    def get_most_active_subjects(self, telegram_id: int, limit: int = 5) -> list[dict]:
        """
        Получить наиболее активные предметы (детальная аналитика для Premium).

        Args:
            telegram_id: Telegram ID пользователя
            limit: Максимальное количество предметов

        Returns:
            List[Dict]: Список предметов с активностью
        """
        from sqlalchemy import select

        from bot.models import ChatHistory

        # Получаем все сообщения пользователя
        messages = (
            self.db.execute(
                select(ChatHistory.message_text)
                .where(ChatHistory.user_telegram_id == telegram_id)
                .where(ChatHistory.message_type == "user")
            )
            .scalars()
            .all()
        )

        subject_keywords = {
            "математика": ["математик", "алгебр", "геометр", "уравнен", "задач"],
            "русский": ["русск", "грамматик", "орфограф"],
            "английский": ["английск", "english"],
            "физика": ["физик", "механик"],
            "химия": ["хими", "реакц"],
            "биология": ["биолог"],
            "география": ["географ"],
            "история": ["истори"],
        }

        subject_counts = {}
        for message in messages:
            message_lower = message.lower()
            for subject, keywords in subject_keywords.items():
                if any(kw in message_lower for kw in keywords):
                    subject_counts[subject] = subject_counts.get(subject, 0) + 1
                    break

        # Сортируем по активности
        sorted_subjects = sorted(subject_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

        return [{"subject": subject, "message_count": count} for subject, count in sorted_subjects]

    def get_learning_trends(self, telegram_id: int) -> dict:
        """
        Получить тренды обучения (детальная аналитика для Premium).

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Dict: Тренды обучения
        """
        from datetime import datetime, timedelta

        from sqlalchemy import func, select

        from bot.models import ChatHistory

        now = datetime.now(UTC)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Сообщения за неделю
        week_count = (
            self.db.scalar(
                select(func.count(ChatHistory.id))
                .where(ChatHistory.user_telegram_id == telegram_id)
                .where(ChatHistory.timestamp >= week_ago)
            )
            or 0
        )

        # Сообщения за месяц
        month_count = (
            self.db.scalar(
                select(func.count(ChatHistory.id))
                .where(ChatHistory.user_telegram_id == telegram_id)
                .where(ChatHistory.timestamp >= month_ago)
            )
            or 0
        )

        # Вычисляем тренд
        if month_count > 0:
            weekly_avg = month_count / 4
            trend = "increasing" if week_count > weekly_avg else "decreasing"
        else:
            trend = "stable"

        return {
            "messages_last_week": week_count,
            "messages_last_month": month_count,
            "trend": trend,
            "weekly_average": month_count / 4 if month_count > 0 else 0,
        }
