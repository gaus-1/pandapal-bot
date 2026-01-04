"""
Сервис для проверки и применения Premium функций.

Обеспечивает проверку premium статуса и применение ограничений
для бесплатных пользователей согласно обещаниям на frontend.
"""

from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from bot.services.subscription_service import SubscriptionService


class PremiumFeaturesService:
    """
    Сервис для работы с Premium функциями.

    Проверяет premium статус и применяет ограничения для бесплатных пользователей.
    """

    # Лимиты для бесплатных пользователей
    FREE_AI_REQUESTS_PER_DAY = 20  # 20 запросов в день для бесплатных
    FREE_SUBJECTS_LIMIT = 3  # Только 3 предмета для бесплатных
    FREE_ANALYTICS_BASIC = True  # Базовая аналитика доступна всем
    FREE_ANALYTICS_DETAILED = False  # Детальная аналитика только для premium

    def __init__(self, db: Session):
        """
        Инициализация сервиса.

        Args:
            db: Сессия SQLAlchemy
        """
        self.db = db
        self.subscription_service = SubscriptionService(db)

    def is_premium_active(self, telegram_id: int) -> bool:
        """
        Проверка активной Premium подписки.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            bool: True если есть активная подписка
        """
        return self.subscription_service.is_premium_active(telegram_id)

    def get_premium_plan(self, telegram_id: int) -> Optional[str]:
        """
        Получить тип активной Premium подписки.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Optional[str]: Тип плана ('week', 'month', 'year') или None
        """
        subscription = self.subscription_service.get_active_subscription(telegram_id)
        return subscription.plan_id if subscription else None

    def can_make_ai_request(self, telegram_id: int) -> tuple[bool, Optional[str]]:
        """
        Проверка возможности сделать AI запрос.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            tuple[bool, Optional[str]]: (разрешено, причина отказа)
        """
        if self.is_premium_active(telegram_id):
            # Premium пользователи - неограниченные запросы
            return True, None

        # Для бесплатных проверяем дневной лимит
        from datetime import datetime, timezone

        from sqlalchemy import func, select

        from bot.models import ChatHistory

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        # Подсчитываем запросы за сегодня
        stmt = (
            select(func.count(ChatHistory.id))
            .where(ChatHistory.user_telegram_id == telegram_id)
            .where(ChatHistory.message_type == "user")
            .where(ChatHistory.timestamp >= today_start)
        )

        today_requests = self.db.scalar(stmt) or 0

        if today_requests >= self.FREE_AI_REQUESTS_PER_DAY:
            return (
                False,
                f"Дневной лимит бесплатных запросов ({self.FREE_AI_REQUESTS_PER_DAY}) исчерпан. "
                f"Купи Premium для неограниченных запросов!",
            )

        return True, None

    def can_access_subject(self, telegram_id: int, subject_id: str) -> tuple[bool, Optional[str]]:
        """
        Проверка доступа к предмету.

        Args:
            telegram_id: Telegram ID пользователя
            subject_id: ID предмета

        Returns:
            tuple[bool, Optional[str]]: (разрешено, причина отказа)
        """
        if self.is_premium_active(telegram_id):
            # Premium пользователи - доступ ко всем предметам
            return True, None

        # Для бесплатных - ограниченный доступ
        # Базовые предметы доступны всем: математика, русский, английский
        free_subjects = ["math", "russian", "english"]

        if subject_id in free_subjects:
            return True, None

        return (
            False,
            f"Доступ к предмету '{subject_id}' доступен только для Premium пользователей. "
            f"Купи Premium для доступа ко всем предметам!",
        )

    def can_access_detailed_analytics(self, telegram_id: int) -> bool:
        """
        Проверка доступа к детальной аналитике.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            bool: True если доступ разрешен
        """
        return self.is_premium_active(telegram_id)

    def can_access_exclusive_achievements(self, telegram_id: int) -> bool:
        """
        Проверка доступа к эксклюзивным достижениям.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            bool: True если доступ разрешен
        """
        return self.is_premium_active(telegram_id)

    def can_access_priority_support(self, telegram_id: int) -> bool:
        """
        Проверка доступа к приоритетной поддержке.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            bool: True если доступ разрешен
        """
        return self.is_premium_active(telegram_id)

    def can_access_bonus_lessons(self, telegram_id: int) -> bool:
        """
        Проверка доступа к бонусным урокам (только для годовой подписки).

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            bool: True если доступ разрешен
        """
        plan = self.get_premium_plan(telegram_id)
        return plan == "year"

    def has_vip_status(self, telegram_id: int) -> bool:
        """
        Проверка VIP статуса (только для годовой подписки).

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            bool: True если есть VIP статус
        """
        plan = self.get_premium_plan(telegram_id)
        return plan == "year"

    def get_premium_features_status(self, telegram_id: int) -> Dict:
        """
        Получить статус всех Premium функций для пользователя.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Dict: Статус всех функций
        """
        is_premium = self.is_premium_active(telegram_id)
        plan = self.get_premium_plan(telegram_id)

        return {
            "is_premium": is_premium,
            "plan": plan,
            "unlimited_ai_requests": is_premium,
            "all_subjects_access": is_premium,
            "personal_tutor": is_premium,
            "detailed_analytics": is_premium,
            "exclusive_achievements": is_premium,
            "priority_support": is_premium,
            "bonus_lessons": plan == "year",
            "vip_status": plan == "year",
        }
