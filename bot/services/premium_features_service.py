"""
Сервис для проверки и применения Premium функций.

Обеспечивает проверку premium статуса и применение ограничений
для бесплатных пользователей согласно обещаниям на frontend.
"""

from datetime import UTC

from loguru import logger
from sqlalchemy.orm import Session

from bot.config import settings
from bot.services.subscription_service import SubscriptionService


class PremiumFeaturesService:
    """
    Сервис для работы с Premium функциями.

    Проверяет premium статус и применяет ограничения для бесплатных пользователей.
    """

    # Лимиты для разных тарифов
    FREE_AI_REQUESTS_PER_MONTH = 30  # 30 запросов в месяц для бесплатных
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
        - Бесплатные: 30 запросов в месяц (30 дней)
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

        # Для месячного плана проверяем дневной лимит
        if plan == "month":
            from datetime import datetime, timedelta

            from sqlalchemy import func, select

            from bot.models import DailyRequestCount

            today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start.replace(hour=23, minute=59, second=59, microsecond=999999)

            # Получаем счетчик запросов за сегодня
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
            # Бесплатные пользователи - 30 запросов за последние 30 дней
            from datetime import datetime, timedelta

            from sqlalchemy import func, select

            from bot.models import DailyRequestCount

            now = datetime.now(UTC)
            month_ago = now - timedelta(days=30)

            # Суммируем все запросы за последние 30 дней
            stmt = (
                select(func.sum(DailyRequestCount.request_count))
                .where(DailyRequestCount.user_telegram_id == telegram_id)
                .where(DailyRequestCount.date >= month_ago)
            )

            total_requests = self.db.execute(stmt).scalar() or 0

            monthly_limit = self.FREE_AI_REQUESTS_PER_MONTH
            if total_requests >= monthly_limit:
                return (
                    False,
                    f"🐼 Ой! Ты уже использовал все {monthly_limit} бесплатных вопросов в этом месяце!\n\n"
                    f"💎 Узнай больше о Premium и получи дополнительные возможности!\n\n"
                    f"✨ С Premium ты сможешь:\n"
                    f"• Задавать до {self.MONTH_PLAN_AI_REQUESTS_PER_DAY} вопросов в день (месячная подписка)\n"
                    f"• Или без ограничений (годовая подписка)\n"
                    f"• Получать помощь по всем предметам\n"
                    f"• Играть в игры без ограничений\n\n"
                    f"Нажми /premium чтобы узнать больше! 🚀",
                )

        return True, None

    def increment_request_count(self, telegram_id: int) -> tuple[bool, int]:
        """
        Увеличить счетчик запросов пользователя за сегодня.

        Создает или обновляет запись в DailyRequestCount.
        Этот счетчик не зависит от ChatHistory и не сбрасывается при очистке истории.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            tuple[bool, int]: (лимит достигнут, текущее количество запросов за месяц)
        """
        from datetime import datetime, timedelta

        from sqlalchemy import func, select

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

        # Проверяем, достигнут ли месячный лимит для бесплатных пользователей
        plan = self.get_premium_plan(telegram_id)
        if not plan and not self.is_admin(telegram_id):
            month_ago = now - timedelta(days=30)
            stmt = (
                select(func.sum(DailyRequestCount.request_count))
                .where(DailyRequestCount.user_telegram_id == telegram_id)
                .where(DailyRequestCount.date >= month_ago)
            )
            total_requests = self.db.execute(stmt).scalar() or 0
            limit_reached = total_requests >= self.FREE_AI_REQUESTS_PER_MONTH
            return limit_reached, total_requests

        return False, 0

    def get_limit_reached_message_text(self) -> str:
        """
        Текст сообщения от панды при достижении лимита (для добавления в историю чата).

        Returns:
            str: Одно из сообщений о лимите (каноническое для истории).
        """
        return (
            "🐼 Привет! Я заметил, что ты уже использовал все 30 бесплатных вопросов в этом месяце.\n\n"
            "💎 С Premium у тебя будет:\n"
            "• До 500 вопросов в день (месячная подписка)\n"
            "• Или без ограничений (годовая подписка)\n"
            "• Помощь по всем предметам\n"
            "• Игры без ограничений\n\n"
            "✨ Узнай больше: /premium"
        )

    async def send_limit_reached_notification(self, telegram_id: int, bot) -> None:
        """
        Отправить проактивное уведомление от панды при достижении месячного лимита.

        Args:
            telegram_id: Telegram ID пользователя
            bot: Экземпляр Telegram бота (aiogram Bot)
        """
        from bot.models import User

        user = self.db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            return

        # Дружелюбное сообщение от панды без слов "КУПИТЬ" или "КУПИ"
        messages = [
            "🐼 Привет! Я заметил, что ты уже использовал все 30 бесплатных вопросов в этом месяце.\n\n"
            "💎 С Premium у тебя будет:\n"
            "• До 500 вопросов в день (месячная подписка)\n"
            "• Или без ограничений (годовая подписка)\n"
            "• Помощь по всем предметам\n"
            "• Игры без ограничений\n\n"
            "✨ Узнай больше: /premium",
            "🐼 Эй! Ты уже задал все 30 бесплатных вопросов в этом месяце!\n\n"
            "💎 Premium открывает новые возможности:\n"
            "• Много больше вопросов каждый день\n"
            "• Все школьные предметы\n"
            "• Игры без ограничений\n"
            "• Приоритетная поддержка\n\n"
            "🚀 Посмотри что еще есть: /premium",
        ]

        import random

        message = random.choice(messages)

        try:
            await bot.send_message(chat_id=telegram_id, text=message, parse_mode="HTML")
            logger.info(
                f"✅ Проактивное уведомление о лимите отправлено пользователю {telegram_id}"
            )
        except Exception as e:
            logger.error(
                f"❌ Ошибка отправки проактивного уведомления пользователю {telegram_id}: {e}"
            )

    async def send_limit_reached_notification_async(self, telegram_id: int) -> None:
        """
        Асинхронная отправка проактивного уведомления (для фоновых задач).

        Args:
            telegram_id: Telegram ID пользователя
        """
        try:
            from aiogram import Bot

            bot = Bot(token=settings.telegram_bot_token)
            await self.send_limit_reached_notification(telegram_id, bot)
            await bot.session.close()
        except Exception as e:
            logger.error(f"❌ Ошибка отправки проактивного уведомления (async): {e}")

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
            f"Узнай больше о Premium: /premium",
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
