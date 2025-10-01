"""
Сервис модерации контента
Фильтрует запрещённые темы: политика, насилие, наркотики и т.д.
OWASP A04:2021 - Insecure Design (защита детей)
@module bot.services.moderation_service
"""

import re
from typing import Tuple, List, Optional
from bot.config import settings, FORBIDDEN_PATTERNS
from loguru import logger


class ContentModerationService:
    """
    Сервис модерации контента для защиты детей
    Многоуровневая проверка на запрещённые темы
    """
    
    def __init__(self):
        """Инициализация сервиса модерации"""
        self.forbidden_topics = settings.get_forbidden_topics_list()
        self.forbidden_patterns = FORBIDDEN_PATTERNS
        self.filter_level = settings.content_filter_level
    
    def is_safe_content(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Проверка, безопасен ли контент для ребёнка
        
        Args:
            text: Текст для проверки
        
        Returns:
            Tuple[bool, Optional[str]]: (безопасен, причина блокировки)
        
        Example:
            >>> is_safe, reason = moderation.is_safe_content("Помоги с математикой")
            >>> print(is_safe)  # True
            
            >>> is_safe, reason = moderation.is_safe_content("Расскажи про политику")
            >>> print(is_safe)  # False
            >>> print(reason)  # "Обнаружена запрещённая тема: политика"
        """
        if not text:
            return True, None
        
        text_lower = text.lower()
        
        # Уровень 1: Проверка точных совпадений с запрещёнными темами
        for topic in self.forbidden_topics:
            if topic.lower() in text_lower:
                logger.warning(f"🚫 Заблокирован контент: тема '{topic}'")
                return False, f"Обнаружена запрещённая тема: {topic}"
        
        # Уровень 2: Проверка паттернов (более детальная)
        for pattern in self.forbidden_patterns:
            if pattern.lower() in text_lower:
                logger.warning(f"🚫 Заблокирован контент: паттерн '{pattern}'")
                return False, f"Обнаружена запрещённая тема"
        
        # Уровень 3: Проверка на мат и нецензурщину (если filter_level >= 4)
        if self.filter_level >= 4:
            if self._contains_profanity(text_lower):
                logger.warning(f"🚫 Заблокирован контент: обнаружена нецензурная лексика")
                return False, "Пожалуйста, используй вежливые слова"
        
        # Уровень 4: Проверка на подозрительные символы/паттерны
        if self.filter_level >= 5:
            if self._contains_suspicious_patterns(text):
                logger.warning(f"🚫 Заблокирован контент: подозрительные паттерны")
                return False, "Обнаружен потенциально опасный контент"
        
        # Контент безопасен
        return True, None
    
    def _contains_profanity(self, text: str) -> bool:
        """
        Проверка на нецензурную лексику (базовая)
        
        Args:
            text: Текст (уже в нижнем регистре)
        
        Returns:
            bool: True если обнаружен мат
        """
        # Базовый список нецензурных слов (замените на полный словарь)
        profanity_words = [
            'блять', 'бля', 'хуй', 'пизд', 'ебать', 'ебан',
            'сука', 'мудак', 'дебил', 'идиот',
            # Добавьте больше слов или используйте библиотеку better-profanity
        ]
        
        for word in profanity_words:
            if word in text:
                return True
        
        return False
    
    def _contains_suspicious_patterns(self, text: str) -> bool:
        """
        Проверка на подозрительные паттерны
        
        Args:
            text: Текст для проверки
        
        Returns:
            bool: True если обнаружены подозрительные паттерны
        """
        # Проверка на SQL Injection попытки
        sql_patterns = [
            r"('\s*OR\s*'1'\s*=\s*'1)",
            r"(;\s*DROP\s+TABLE)",
            r"(UNION\s+SELECT)",
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Проверка на XSS попытки
        xss_patterns = [
            r"<script.*?>",
            r"javascript:",
            r"on\w+\s*=",  # onclick=, onerror=, etc
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def sanitize_ai_response(self, response: str) -> str:
        """
        Очистка ответа AI от потенциально опасного контента
        Дополнительная проверка на случай, если AI сгенерирует что-то плохое
        
        Args:
            response: Ответ от AI
        
        Returns:
            str: Очищенный ответ
        """
        # Проверяем ответ AI на безопасность
        is_safe, reason = self.is_safe_content(response)
        
        if not is_safe:
            logger.error(f"⚠️ AI сгенерировал небезопасный контент! Причина: {reason}")
            # Возвращаем безопасный fallback ответ
            return "Извини, я не могу ответить на этот вопрос. Давай лучше поговорим об учёбе! 📚"
        
        return response
    
    def get_safe_response_alternative(self, detected_topic: str) -> str:
        """
        Получить безопасный альтернативный ответ при блокировке
        
        Args:
            detected_topic: Обнаруженная запрещённая тема
        
        Returns:
            str: Дружелюбный ответ с перенаправлением на учёбу
        """
        alternatives = [
            "Эта тема не для меня 🐼 Давай лучше поговорим об учёбе!",
            "Я создан помогать с учёбой 📚 Есть вопросы по школьным предметам?",
            "Давай обсудим что-нибудь интересное из школьной программы! 🎓",
            "Я лучше помогу тебе с домашним заданием 😊 Что задали?",
        ]
        
        # Выбираем случайный вариант (или первый)
        import random
        return random.choice(alternatives)
    
    def log_blocked_content(
        self, 
        telegram_id: int, 
        message: str, 
        reason: str
    ) -> None:
        """
        Логирование заблокированного контента
        Важно для мониторинга и улучшения фильтров
        
        Args:
            telegram_id: Telegram ID пользователя
            message: Заблокированное сообщение
            reason: Причина блокировки
        """
        logger.warning(
            f"🚫 BLOCKED CONTENT | "
            f"User: {telegram_id} | "
            f"Reason: {reason} | "
            f"Message: {message[:100]}..."
        )
        
        # TODO: Сохранить в отдельную таблицу moderation_log для аналитики


