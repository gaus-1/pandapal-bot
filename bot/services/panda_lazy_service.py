"""
Сервис для управления "ленивостью" панды.

Отслеживает количество запросов пользователя и делает панду "ленивой"
после 15-20 запросов подряд в течение 20 минут.
"""

import random
from datetime import UTC, datetime, timedelta

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bot.models import ChatHistory, User


class PandaLazyService:
    """
    Сервис для управления состоянием "ленивости" панды.

    Логика:
    - Считает запросы пользователя за последние 20 минут
    - Если >= 15 запросов → панда становится "ленивой" на 10 минут
    - После 10 минут панда снова активна
    """

    # Параметры ленивости
    REQUESTS_THRESHOLD = 15  # Количество запросов для активации ленивости
    TIME_WINDOW_MINUTES = 20  # Окно времени для подсчета запросов
    LAZY_DURATION_MINUTES = 10  # Длительность "ленивости" в минутах

    def __init__(self, db: Session):
        """
        Инициализация сервиса.

        Args:
            db: Сессия SQLAlchemy для работы с базой данных.
        """
        self.db = db

    def check_and_update_lazy_state(self, telegram_id: int) -> tuple[bool, str | None]:
        """
        Проверяет состояние ленивости панды и обновляет его при необходимости.

        Args:
            telegram_id: Telegram ID пользователя.

        Returns:
            tuple: (is_lazy: bool, lazy_message: str | None)
                - is_lazy: True если панда сейчас "ленива"
                - lazy_message: Сообщение для пользователя или None
        """
        # Получаем пользователя
        user = self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        ).scalar_one_or_none()
        if not user:
            return False, None

        now = datetime.now(UTC)

        # Проверяем, не истекла ли текущая "ленивость"
        if user.panda_lazy_until and user.panda_lazy_until > now:
            # Панда все еще "ленива"
            lazy_responses = [
                "Я объелся бамбуком и хочу отдохнуть...Напиши мне чуть-чуть попозже",
                "Как-то лениво мне...пойду немного покувыркаюсь и поем бамбука...",
            ]
            return True, random.choice(lazy_responses)

        # Если время "ленивости" истекло, сбрасываем
        if user.panda_lazy_until and user.panda_lazy_until <= now:
            user.panda_lazy_until = None
            self.db.flush()
            logger.info(f"🐼 Панда снова активна для пользователя {telegram_id}")

        # Считаем запросы за последние 20 минут
        time_threshold = now - timedelta(minutes=self.TIME_WINDOW_MINUTES)
        request_count = (
            self.db.execute(
                select(func.count(ChatHistory.id))
                .where(ChatHistory.user_telegram_id == telegram_id)
                .where(ChatHistory.message_type == "user")
                .where(ChatHistory.timestamp >= time_threshold)
            ).scalar()
            or 0
        )

        logger.info(
            f"📊 Пользователь {telegram_id}: {request_count} запросов за последние {self.TIME_WINDOW_MINUTES} минут"
        )

        # Если достигли порога, активируем "ленивость"
        if request_count >= self.REQUESTS_THRESHOLD:
            lazy_until = now + timedelta(minutes=self.LAZY_DURATION_MINUTES)
            user.panda_lazy_until = lazy_until
            self.db.flush()
            logger.info(f"😴 Панда стала 'ленивой' для пользователя {telegram_id} до {lazy_until}")

            lazy_responses = [
                "Я объелся бамбуком и хочу отдохнуть...Напиши мне чуть-чуть попозже",
                "Как-то лениво мне...пойду немного покувыркаюсь и поем бамбука...",
            ]
            return True, random.choice(lazy_responses)

        return False, None
