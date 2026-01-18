"""
Сервис для проверки и применения Premium функций.

Обеспечивает проверку premium статуса и применение ограничений
для бесплатных пользователей согласно обещаниям на frontend.
"""

from datetime import UTC

from sqlalchemy.orm import Session

from bot.config import settings
from bot.services.subscription_service import SubscriptionService


class PremiumFeaturesService:
    """
    Сервис для работы с Premium функциями.

    Проверяет premium статус и применяет ограничения для бесплатных пользователей.
    """

    # Лимиты для разных тарифов
    FREE_AI_REQUESTS_PER_DAY = 30  # 30 запросов в день для бесплатных
    MONTH_PLAN_AI_REQUESTS_PER_DAY = 500  # 500 запросов в день для месячного плана (399₽)
    # Годовая подписка - без ограничений (неограниченные запросы)
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

    def is_admin(self, telegram_id: int, username: str | None = None) -> bool:
        """
        Проверка, является ли пользователь админом.

        Args:
            telegram_id: Telegram ID пользователя
            username: Username пользователя (опционально, для проверки)

        Returns:
            bool: True если пользователь админ
        """
        if not username:
            # Получаем username из БД
            from bot.models import User

            user = self.db.query(User).filter(User.telegram_id == telegram_id).first()
            if user and user.username:
                username = user.username

        if username:
            admin_list = settings.get_admin_usernames_list()
            return username.lower() in admin_list

        return False

    def is_premium_active(self, telegram_id: int) -> bool:
        """
        Проверка активной Premium подписки.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            bool: True если есть активная подписка
        """
        return self.subscription_service.is_premium_active(telegram_id)

    def get_premium_plan(self, telegram_id: int) -> str | None:
        """
        Получить тип активной Premium подписки.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Optional[str]: Тип плана ('month', 'year') или None
        """
        subscription = self.subscription_service.get_active_subscription(telegram_id)
        return subscription.plan_id if subscription else None

    def can_make_ai_request(
        self, telegram_id: int, username: str | None = None
    ) -> tuple[bool, str | None]:
        """
        Проверка возможности сделать AI запрос.

        Лимиты по тарифам:
        - Бесплатные: 30 запросов в день
        - Месячный план (399₽): 500 запросов в день
        - Годовая подписка: без ограничений
        - Админы: без ограничений

        Использует DailyRequestCount для подсчета, который не зависит от ChatHistory.
        Это предотвращает обход лимита через удаление истории.

        Args:
            telegram_id: Telegram ID пользователя
            username: Username пользователя (опционально, для проверки админа)

        Returns:
            tuple[bool, Optional[str]]: (разрешено, причина отказа)
        """
        # Админы - неограниченные запросы
        if self.is_admin(telegram_id, username):
            return True, None

        # Проверяем Premium статус и план
        plan = self.get_premium_plan(telegram_id)

        # Годовая подписка - без ограничений
        if plan == "year":
            return True, None

        # Для всех остальных проверяем дневной лимит через DailyRequestCount
        from datetime import datetime

        from sqlalchemy import select

        from bot.models import DailyRequestCount

        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Получаем счетчик запросов за сегодня (точное совпадение по дате)
        stmt = (
            select(DailyRequestCount)
            .where(DailyRequestCount.user_telegram_id == telegram_id)
            .where(DailyRequestCount.date >= today_start)
            .where(DailyRequestCount.date < today_end)
            .order_by(DailyRequestCount.date.desc())
            .limit(1)
        )

        today_counter = self.db.execute(stmt).scalar_one_or_none()
        today_requests = today_counter.request_count if today_counter else 0

        # Определяем лимит в зависимости от плана
        if plan == "month":
            # Месячный план (399₽) - 500 запросов в день
            daily_limit = self.MONTH_PLAN_AI_REQUESTS_PER_DAY
            if today_requests >= daily_limit:
                return (
                    False,
                    f"🐼 Ой! Ты уже использовал все {daily_limit} запросов сегодня!\n\n"
                    f"💎 Чтобы задавать вопросы без ограничений, перейди на годовую подписку!\n\n"
                    f"✨ С годовой подпиской ты сможешь:\n"
                    f"• Задавать сколько угодно вопросов\n"
                    f"• Получать помощь по всем предметам\n"
                    f"• Играть в игры без ограничений\n\n"
                    f"Нажми /premium чтобы узнать больше! 🚀",
                )
        else:
            # Бесплатные пользователи - 30 запросов в день
            daily_limit = self.FREE_AI_REQUESTS_PER_DAY
            if today_requests >= daily_limit:
                return (
                    False,
                    f"🐼 Ой! Ты уже использовал все {daily_limit} бесплатных вопросов сегодня!\n\n"
                    f"💎 Узнай больше о Premium и получи дополнительные возможности!\n\n"
                    f"✨ С Premium ты сможешь:\n"
                    f"• Задавать до {self.MONTH_PLAN_AI_REQUESTS_PER_DAY} вопросов в день (месячная подписка)\n"
                    f"• Или без ограничений (годовая подписка)\n"
                    f"• Получать помощь по всем предметам\n"
                    f"• Играть в игры без ограничений\n\n"
                    f"Нажми /premium чтобы узнать больше! 🚀",
                )

        return True, None

    def increment_request_count(self, telegram_id: int) -> None:
        """
        Увеличить счетчик запросов пользователя за сегодня.

        Создает или обновляет запись в DailyRequestCount.
        Этот счетчик не зависит от ChatHistory и не сбрасывается при очистке истории.

        Args:
            telegram_id: Telegram ID пользователя
        """
        from datetime import datetime

        from sqlalchemy import select

        from bot.models import DailyRequestCount

        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Ищем существующую запись за сегодня (точное совпадение по дате)
        stmt = (
            select(DailyRequestCount)
            .where(DailyRequestCount.user_telegram_id == telegram_id)
            .where(DailyRequestCount.date >= today_start)
            .where(DailyRequestCount.date < today_end)
            .order_by(DailyRequestCount.date.desc())
            .limit(1)
        )

        counter = self.db.execute(stmt).scalar_one_or_none()

        if counter:
            # Обновляем существующую запись
            counter.request_count += 1
            counter.last_request_at = now
        else:
            # Создаем новую запись
            counter = DailyRequestCount(
                user_telegram_id=telegram_id,
                date=today_start,
                request_count=1,
                last_request_at=now,
            )
            self.db.add(counter)

        self.db.flush()

    def can_access_subject(
        self, telegram_id: int, subject_id: str, username: str | None = None
    ) -> tuple[bool, str | None]:
        """
        Проверка доступа к предмету.

        Args:
            telegram_id: Telegram ID пользователя
            subject_id: ID предмета
            username: Username пользователя (опционально, для проверки админа)

        Returns:
            tuple[bool, Optional[str]]: (разрешено, причина отказа)
        """
        # Админы - доступ ко всем предметам
        if self.is_admin(telegram_id, username):
            return True, None

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

    def get_premium_features_status(self, telegram_id: int) -> dict:
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
