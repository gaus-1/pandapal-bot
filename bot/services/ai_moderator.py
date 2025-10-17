"""
Модерация контента для обеспечения безопасности детей.

Этот модуль реализует базовую модерацию контента, следуя принципу
Single Responsibility. Проверяет текстовые сообщения на наличие
запрещенных тем и паттернов для защиты детей от неподходящего контента.

Основные возможности:
- Проверка текста на запрещенные паттерны
- Фильтрация неподходящего контента
- Логирование заблокированных сообщений
- Возврат причин блокировки

Безопасность:
- Проверка на запрещенные темы
- Фильтрация нецензурной лексики
- Защита от неподходящего контента
- Логирование всех блокировок

Принципы:
- Single Responsibility: только модерация контента
- Open/Closed: легко расширяется новыми паттернами
- Interface Segregation: минимальный интерфейс IModerator
"""

from typing import Tuple

from loguru import logger

from bot.config import FORBIDDEN_PATTERNS
from bot.services.ai_response_generator_solid import IModerator


class ContentModerator(IModerator):
    """
    Модератор контента для обеспечения безопасности детей.

    Реализует базовую проверку текстовых сообщений на наличие
    запрещенных паттернов и тем. Следует принципу Single Responsibility
    - единственная задача: модерация контента.
    """

    def moderate(self, text: str) -> Tuple[bool, str]:
        """
        Проверка контента на безопасность.

        Анализирует текст на наличие запрещенных паттернов и тем,
        возвращает результат проверки и причину блокировки (если есть).

        Args:
            text (str): Текст для проверки.

        Returns:
            Tuple[bool, str]: (безопасен, причина_блокировки).
        """
        import re

        text_lower = text.lower()

        # Проверяем учебный контекст
        educational_keywords = ["умножение", "таблица", "математика", "задача", "урок", "учеба"]
        if any(keyword in text_lower for keyword in educational_keywords):
            return True, "Учебный контекст - безопасен"

        for pattern in FORBIDDEN_PATTERNS:
            pattern_lower = pattern.lower()
            # Ищем целое слово с границами \b для избежания ложных срабатываний
            # Например, "нож" не должен находиться в "умножение"
            if re.search(r"\b" + re.escape(pattern_lower) + r"\b", text_lower):
                logger.warning(f"🚫 Запрещенный контент: {pattern}")
                return False, f"Запрещенная тема: {pattern}"

        return True, "Контент безопасен"
