"""
Сервис модерации контента
Фильтрует запрещённые темы: политика, насилие, наркотики и т.д.
OWASP A04:2021 - Insecure Design (защита детей)
@module bot.services.moderation_service
"""

import re
from typing import Tuple, List, Optional, Pattern
from bot.config import settings, FORBIDDEN_PATTERNS
from loguru import logger


class ContentModerationService:
    """
    Сервис модерации контента для защиты детей
    Многоуровневая проверка на запрещённые темы
    """

    def __init__(self) -> None:
        """Инициализация сервиса модерации."""
        # Список запрещённых тем из настроек -> компилируем в word-boundary regex
        topics: List[str] = settings.get_forbidden_topics_list()
        self._topic_regexes: List[Pattern[str]] = [
            re.compile(rf"\b{re.escape(topic)}\b", re.IGNORECASE)
            for topic in topics
        ]

        # Паттерны высокого уровня из конфигурации -> компилируем
        self._forbidden_regexes: List[Pattern[str]] = [
            re.compile(pattern, re.IGNORECASE) for pattern in FORBIDDEN_PATTERNS
        ]

        self.filter_level: int = settings.content_filter_level

        # Базовый список нецензурных слов -> единый regex с word-boundaries
        profanity_words = [
            'блять', 'бля', 'хуй', 'пизд', 'ебать', 'ебан',
            'сука', 'мудак', 'дебил', 'идиот',
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
        Проверка, безопасен ли контент для ребёнка.

        Args:
            text: Текст для проверки

        Returns:
            Tuple[bool, Optional[str]]: (безопасен, причина блокировки)
        """
        if not text:
            return True, None

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

        return True, None

    def sanitize_ai_response(self, response: str) -> str:
        """
        Очистка ответа AI от потенциально опасного контента.
        """
        is_safe, reason = self.is_safe_content(response)
        if not is_safe:
            logger.error(
                f"⚠️ AI сгенерировал небезопасный контент! Причина: {reason}"
            )
            return (
                "Извини, я не могу ответить на этот вопрос. "
                "Давай лучше поговорим об учёбе! 📚"
            )
        return response

    def get_safe_response_alternative(self, detected_topic: str) -> str:
        """Получить безопасный альтернативный ответ при блокировке."""
        alternatives = [
            "Эта тема не для меня 🐼 Давай лучше поговорим об учёбе!",
            "Я создан помогать с учёбой 📚 Есть вопросы по школьным предметам?",
            "Давай обсудим что-нибудь интересное из школьной программы! 🎓",
            "Я лучше помогу тебе с домашним заданием 😊 Что задали?",
        ]
        import random
        return random.choice(alternatives)

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
        # TODO: Сохранить в таблицу moderation_log


