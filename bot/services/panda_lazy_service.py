"""
Сервис для управления "ленивостью" и отдыхом панды.

- Отдых: после 10 ответов подряд панда предлагает игру; после 20 ещё — снова;
  если пользователь снова просит отвечать — включается ленивая панда.
- Ленивость: после 15 запросов за 20 минут панда "отдыхает" 10 минут.
"""

import random
import re
from datetime import UTC, datetime, timedelta

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bot.models import ChatHistory, User

# Фразы, по которым считаем, что пользователь хочет продолжать учиться, а не играть
CONTINUE_LEARN_PATTERNS = re.compile(
    r"(не\s+хочу\s+играть|хочу\s+учиться|продолжай|отвечай|давай\s+дальше|"
    r"не\s+буду\s+играть|давай\s+учиться|отвечай\s+на\s+вопросы|продолжим|ещё\s+вопрос|"
    r"нужно\s+ещё|помоги\s+ещё|не\s+поиграем|давай\s+продолжим|хочу\s+ещё\s+задавать|"
    r"давай\s+решать\s+задачи|решать\s+задачи|решаем\s+задачи|задачи\s+по|"
    r"хочу\s+решать|помоги\s+с\s+задачей|задачи\s+по\s+(математике|геометрии|алгебре|физике)|"
    r"как\s+решать|помоги\s+решить|давай\s+задачи|учебн|учёба|урок|домашк|дз\b)",
    re.IGNORECASE,
)


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

        # Нормализуем panda_lazy_until для сравнения (SQLite хранит naive UTC)
        lazy_until = user.panda_lazy_until
        if lazy_until is not None and lazy_until.tzinfo is None:
            lazy_until = lazy_until.replace(tzinfo=UTC)

        # Проверяем, не истекла ли текущая "ленивость"
        if lazy_until and lazy_until > now:
            # Панда все еще "ленива"
            lazy_responses = [
                "Я объелся бамбуком и хочу отдохнуть...Напиши мне чуть-чуть попозже",
                "Как-то лениво мне...пойду немного покувыркаюсь и поем бамбук...",
            ]
            return True, random.choice(lazy_responses)

        # Если время "ленивости" истекло, сбрасываем
        if lazy_until and lazy_until <= now:
            user.panda_lazy_until = None
            self.db.flush()
            logger.info(f"🐼 Панда снова активна для пользователя {telegram_id}")

        # Считаем запросы за последние 20 минут (naive UTC для совместимости с SQLite)
        time_threshold = (now - timedelta(minutes=self.TIME_WINDOW_MINUTES)).replace(tzinfo=None)
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

    # Пороги для предложения отдыха и игры
    REST_OFFER_AFTER_FIRST = 10  # первый отдых после 10 ответов подряд
    REST_OFFER_AFTER_SECOND = 20  # второй отдых ещё через 20 ответов

    def check_rest_offer(
        self, telegram_id: int, user_message: str, user_first_name: str | None
    ) -> tuple[str | None, bool]:
        """
        Проверка: нужно ли предложить отдых/игру или ответ «продолжаем/играем».

        Returns:
            (response_text, skip_ai): если response_text не None — отправить его и не вызывать AI.
            skip_ai=True — не увеличивать consecutive_since_rest (ответ был отдых/ок продолжать).
        """
        user = self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        ).scalar_one_or_none()
        if not user:
            return None, False

        # Поддержка старых миграций: поля могут отсутствовать
        consecutive = getattr(user, "consecutive_since_rest", 0)
        rest_offers = getattr(user, "rest_offers_count", 0)
        last_was_rest = getattr(user, "last_ai_was_rest", False)

        name = (user_first_name or user.first_name or "").strip() or "друг"
        msg_lower = (user_message or "").strip().lower()

        # Поля отдыха могут отсутствовать до применения миграции
        if not hasattr(user, "last_ai_was_rest"):
            return None, False

        # Пользователь отвечает на предложение отдыха/игры
        if last_was_rest:
            user.last_ai_was_rest = False
            self.db.flush()

            wants_continue = bool(CONTINUE_LEARN_PATTERNS.search(msg_lower))

            if wants_continue and rest_offers >= 2:
                # Второй раз попросил продолжать — включаем ленивую панду
                now = datetime.now(UTC)
                user.panda_lazy_until = now + timedelta(minutes=self.LAZY_DURATION_MINUTES)
                user.rest_offers_count = 0
                user.consecutive_since_rest = 0
                self.db.flush()
                logger.info(f"😴 Панда перешла в режим отдыха для пользователя {telegram_id}")
                lazy_msgs = [
                    "Я объелся бамбуком и хочу отдохнуть...Напиши мне чуть-чуть попозже",
                    "Как-то лениво мне...пойду немного покувыркаюсь и поем бамбука...",
                ]
                return random.choice(lazy_msgs), True

            if wants_continue:
                user.consecutive_since_rest = 0
                self.db.flush()
                return "Хорошо, давай продолжать! Чем могу помочь?", True

            # Хочет играть или просто написал что-то ещё
            user.consecutive_since_rest = 0
            self.db.flush()
            return (
                "Отлично! Заходи в раздел Игры — там крестики-нолики, 2048, шашки и другие игры.",
                True,
            )

        # Проверка: пора ли предложить отдых
        need_first_rest = rest_offers == 0 and consecutive >= self.REST_OFFER_AFTER_FIRST
        need_second_rest = rest_offers == 1 and consecutive >= self.REST_OFFER_AFTER_SECOND

        if need_first_rest or need_second_rest:
            user.rest_offers_count = rest_offers + 1
            user.last_ai_was_rest = True
            self.db.flush()
            rest_phrases = [
                f"Я хочу отдохнуть, {name}, может поиграем?",
                "Может сделаем перерыв и поиграем?",
            ]
            return random.choice(rest_phrases), True

        return None, False

    def increment_consecutive_after_ai(self, telegram_id: int) -> None:
        """Увеличить счётчик ответов подряд после сохранения обычного ответа AI."""
        user = self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        ).scalar_one_or_none()
        if not user or not hasattr(user, "consecutive_since_rest"):
            return
        user.consecutive_since_rest = (user.consecutive_since_rest or 0) + 1
        self.db.flush()
