"""
Сервис модерации контента
Фильтрует запрещённые темы: политика, насилие, наркотики и т.д.
OWASP A04:2021 - Insecure Design (защита детей)

"""

import asyncio
import re
from typing import Any, Dict, List, Optional, Pattern, Tuple

from loguru import logger

from bot.config import FORBIDDEN_PATTERNS, settings
from bot.services.advanced_moderation import AdvancedModerationService, ModerationResult


class ContentModerationService:
    """
    Сервис модерации контента для защиты детей
    Многоуровневая проверка на запрещённые темы
    """

    def __init__(self) -> None:
        """Инициализация сервиса модерации."""
        # Список запрещённых тем из настроек -> компилируем в простой regex для кириллицы
        topics: List[str] = settings.get_forbidden_topics_list()
        self._topic_regexes: List[Pattern[str]] = [
            re.compile(rf"{re.escape(topic)}", re.IGNORECASE) for topic in topics
        ]

        # Паттерны высокого уровня из конфигурации -> компилируем с границами слов
        self._forbidden_regexes: List[Pattern[str]] = [
            re.compile(rf"\b{re.escape(pattern)}\b", re.IGNORECASE)
            for pattern in FORBIDDEN_PATTERNS
        ]

        self.filter_level: int = settings.content_filter_level

        # Инициализируем продвинутый сервис модерации
        self.advanced_moderation = AdvancedModerationService()

        # Базовый список нецензурных слов -> единый regex с word-boundaries
        profanity_words = [
            "блять",
            "бля",
            "хуй",
            "пизд",
            "ебать",
            "ебан",
            "сука",
            "мудак",
            "дебил",
            "идиот",
        ]
        self._profanity_regex: Pattern[str] = re.compile(
            r"|".join(rf"\b{re.escape(w)}\w*\b" for w in profanity_words),
            re.IGNORECASE,
        )

        # SQLi/XSS паттерны
        self._sql_regexes: List[Pattern[str]] = [
            re.compile(r"'\s*OR\s*'1'\s*=\s*'1", re.IGNORECASE),
            re.compile(r";\s*DROP\s+TABLE", re.IGNORECASE),
            re.compile(r"UNION\s+SELECT", re.IGNORECASE),
        ]
        self._xss_regexes: List[Pattern[str]] = [
            re.compile(r"<script.*?>", re.IGNORECASE),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),  # onclick=, onerror=
        ]

    def is_safe_content(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Проверка, безопасен ли контент для ребёнка (базовая версия).

        Args:
            text: Текст для проверки

        Returns:
            Tuple[bool, Optional[str]]: (безопасен, причина блокировки)
        """
        if not text:
            return True, None

        text_lower = text.lower()

        # ИСКЛЮЧЕНИЯ: разрешаем школьные предметы и учебные темы
        educational_contexts = [
            "история россии",
            "история древнего мира",
            "история средних веков",
            "расскажи про историю",
            "объясни историю",
            "помоги с историей",
            "география россии",
            "география мира",
            "физика",
            "химия",
            "биология",
            "математика",
            "русский язык",
            "литература",
            "английский язык",
            "урок",
            "домашнее задание",
            "контрольная работа",
            "экзамен",
            "школьная программа",
            "учебник",
            "учеба",
            "обучение",
            # Математические задачи
            "задача",
            "решить",
            "сколько",
            "вычисли",
            "посчитай",
            "найди",
            "докажи",
            "вместе",
            "было",
            "таблица умножения",
            "таблица",
            "умножение",
            "деление",
            "сложение",
            "вычитание",
            # Русский язык
            "подчеркни",
            "слово",
            "предложение",
            "согласная",
            "гласная",
            "твердый",
            "мягкий",
            "алфавит",
            "буква",
            "азбука",
            # Учебные материалы
            "шпаргалка",
            "памятка",
            "справка",
            "правило",
            "формула",
            "создай",
            "напиши",
            "покажи",
            "объясни",
        ]

        # Уровень 1: Проверка точных тем (по словам)
        for rx in self._topic_regexes:
            if rx.search(text):
                logger.warning("🚫 Заблокирован контент: тема запрещена")
                return False, "Обнаружена запрещённая тема"

        # Уровень 2: Проверка паттернов из общего списка
        for rx in self._forbidden_regexes:
            if rx.search(text):
                logger.warning("🚫 Заблокирован контент: общий паттерн")
                return False, "Обнаружена запрещённая тема"

        # Уровень 3: Нецензурная лексика
        if self.filter_level >= 4 and self._profanity_regex.search(text):
            logger.warning("🚫 Заблокирован контент: нецензурная лексика")
            return False, "Пожалуйста, используй вежливые слова"

        # Уровень 4: Тех. паттерны (SQLi/XSS)
        if self.filter_level >= 5:
            if any(rx.search(text) for rx in self._sql_regexes):
                logger.warning("🚫 Заблокирован контент: SQL injection pattern")
                return False, "Обнаружен потенциально опасный контент"
            if any(rx.search(text) for rx in self._xss_regexes):
                logger.warning("🚫 Заблокирован контент: XSS pattern")
                return False, "Обнаружен потенциально опасный контент"

        # Дополнительная проверка: если контент содержит учебные слова, но прошёл все проверки - разрешаем
        if any(context in text_lower for context in educational_contexts):
            logger.info(f"✅ Разрешен учебный контекст: {text[:50]}...")

        return True, None

    def sanitize_ai_response(self, response: str) -> str:
        """
        Очистка ответа AI от потенциально опасного контента.
        """
        is_safe, reason = self.is_safe_content(response)
        if not is_safe:
            logger.error(f"⚠️ AI сгенерировал небезопасный контент! Причина: {reason}")
            return "Извини, я не могу ответить на этот вопрос. " "Давай лучше поговорим об учёбе! 📚"
        return response

    def get_safe_response_alternative(self, detected_topic: str) -> str:
        """Получить безопасный альтернативный ответ при блокировке."""
        alternatives = [
            "Извини, но я не могу ответить на этот вопрос. Моя задача — помогать тебе с учебой, творчеством и другими полезными и безопасными темами! 🐼",
            "Эта тема не подходит для нашего общения. Давай лучше поговорим об учёбе или интересных школьных предметах! 📚",
            "Я создан помогать детям с учёбой и безопасными вопросами. Есть вопросы по математике, русскому языку или другим предметам? 🎓",
            "Давай обсудим что-нибудь интересное из школьной программы! Я могу помочь с домашним заданием 😊",
            "Я не могу обсуждать такие темы. Моя цель — сделать обучение интересным и безопасным! Что изучаем сегодня? ✨",
        ]
        import random

        return random.choice(alternatives)

    async def _save_moderation_log(self, telegram_id: int, content: str, reason: str) -> None:
        """Сохранить лог модерации в базу данных"""
        try:
            from datetime import datetime

            from sqlalchemy import select

            from bot.database import get_db
            from bot.models import User

            async with get_db() as db:
                # Получаем пользователя
                stmt = select(User).where(User.telegram_id == telegram_id)
                user = await db.execute(stmt)
                user_obj = user.scalar_one_or_none()

                if user_obj:
                    # Здесь можно добавить таблицу moderation_log в будущем
                    # Пока логируем через стандартный логгер
                    logger.info(
                        "MODERATION_LOG | User: %s | Reason: %s | Content: %s | Time: %s",
                        telegram_id,
                        reason,
                        content[:100] + "..." if len(content) > 100 else content,
                        datetime.utcnow().isoformat(),
                    )
        except Exception as e:
            logger.error(f"Ошибка сохранения лога модерации: {e}")

    def log_blocked_content(self, telegram_id: int, message: str, reason: str) -> None:
        """
        Логирование заблокированного контента для мониторинга и аналитики.
        """
        logger.warning(
            "🚫 BLOCKED CONTENT | User: %s | Reason: %s | Message: %s",
            telegram_id,
            reason,
            message[:100] + "...",
        )
        # Сохраняем в таблицу moderation_log (синхронно через логгер)
        # В будущем можно добавить асинхронное сохранение в БД

    async def advanced_moderate_content(
        self, content: str, user_context: Dict[str, Any] = None
    ) -> ModerationResult:
        """
        Продвинутая модерация контента с использованием ML и контекстного анализа.

        Args:
            content: Текст для проверки
            user_context: Контекст пользователя (возраст, история и т.д.)

        Returns:
            ModerationResult: Детальный результат анализа
        """
        return await self.advanced_moderation.moderate_content(content, user_context)

    async def get_moderation_stats(self) -> Dict[str, Any]:
        """Возвращает статистику модерации"""
        return await self.advanced_moderation.get_moderation_stats()
