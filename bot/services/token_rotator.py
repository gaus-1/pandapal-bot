"""
Сервис ротации API токенов Gemini AI.

Этот модуль реализует автоматическое переключение между несколькими API ключами
Google Gemini для обхода лимитов запросов. Поддерживает циклическую ротацию,
отслеживание неудачных токенов и автоматический retry при ошибках квоты.

Основные возможности:
- Управление множественными API ключами
- Автоматическое переключение при исчерпании квоты
- Отслеживание статистики использования
- Сброс неудачных токенов (например, в новом дне)
"""

import asyncio
import random
from typing import List, Optional

from loguru import logger

from bot.config import settings


class TokenRotator:
    """
    Ротатор API токенов для автоматического переключения между ключами Gemini AI.

    Обеспечивает непрерывную работу бота при исчерпании квоты отдельных токенов
    путем автоматического переключения на следующий доступный ключ.

    Attributes:
        tokens (List[str]): Список всех доступных API токенов.
        current_index (int): Индекс текущего активного токена.
        failed_tokens (Set[str]): Множество токенов, помеченных как неудачные.
    """

    def __init__(self):
        """
        Инициализация ротатора токенов.

        Загружает все доступные токены из конфигурации и настраивает
        начальное состояние для циклической ротации.
        """
        self.tokens = self._prepare_tokens()
        self.current_index = 0
        self.failed_tokens = set()  # Токены, которые не работают

        logger.info(f"🔄 Token Rotator инициализирован с {len(self.tokens)} токенами")

    def _prepare_tokens(self) -> List[str]:
        """
        Подготовка и валидация списка токенов из конфигурации.

        Загружает основной токен и дополнительные токены из переменных окружения,
        разбивает строку дополнительных токенов по запятым и удаляет дубликаты.

        Returns:
            List[str]: Отсортированный список уникальных токенов.

        Raises:
            ValueError: Если не найдено ни одного валидного токена.
        """
        tokens = []

        # Основной токен
        if settings.gemini_api_key:
            tokens.append(settings.gemini_api_key.strip())

        # Дополнительные токены (из строки через запятую)
        if settings.gemini_api_keys:
            # Разбиваем строку по запятой и очищаем от пробелов
            additional_tokens = [
                token.strip() for token in settings.gemini_api_keys.split(",") if token.strip()
            ]
            tokens.extend(additional_tokens)

        # Убираем дубликаты
        tokens = list(dict.fromkeys(tokens))

        if not tokens:
            logger.warning("⚠️ Нет доступных API токенов!")

        return tokens

    def get_current_token(self) -> Optional[str]:
        """
        Получить текущий активный токен.

        Возвращает токен, который должен использоваться для следующего запроса.
        Автоматически переключается на следующий токен, если текущий помечен как неудачный.

        Returns:
            Optional[str]: Текущий активный токен или None, если все токены исчерпаны.
        """
        if not self.tokens:
            return None

        available_tokens = [t for t in self.tokens if t not in self.failed_tokens]

        if not available_tokens:
            logger.error("❌ Все токены исчерпаны!")
            return None

        # Если текущий токен в списке неудачных, переключаемся
        if self.tokens[self.current_index] in self.failed_tokens:
            self.current_index = (self.current_index + 1) % len(self.tokens)

        return self.tokens[self.current_index]

    def mark_token_failed(self, token: str, reason: str = "quota_exceeded") -> None:
        """
        Пометить токен как неудачный и переключиться на следующий.

        Args:
            token (str): Токен, который следует пометить как неудачный.
            reason (str): Причина неудачи (по умолчанию "quota_exceeded").
        """
        if token in self.tokens:
            self.failed_tokens.add(token)
            logger.warning(f"⚠️ Токен помечен как неудачный: {reason}")

            # Переключаемся на следующий токен
            self.next_token()

    def next_token(self) -> Optional[str]:
        """
        Переключиться на следующий токен в циклическом порядке.

        Returns:
            Optional[str]: Следующий доступный токен или None, если нет токенов.
        """
        if not self.tokens:
            return None

        self.current_index = (self.current_index + 1) % len(self.tokens)
        return self.get_current_token()

    def reset_failed_tokens(self) -> None:
        """
        Сбросить список неудачных токенов.

        Используется для восстановления всех токенов, например, в начале нового дня,
        когда квоты сбрасываются.
        """
        self.failed_tokens.clear()
        logger.info("🔄 Список неудачных токенов сброшен")

    def get_stats(self) -> dict:
        """
        Получить статистику использования токенов.

        Returns:
            dict: Словарь со статистикой:
                - total_tokens (int): Общее количество токенов
                - available_tokens (int): Количество доступных токенов
                - failed_tokens (int): Количество неудачных токенов
                - current_index (int): Индекс текущего токена
                - current_token (str): Текущий токен (маскированный)
        """
        total = len(self.tokens)
        failed = len(self.failed_tokens)
        available = total - failed

        return {
            "total_tokens": total,
            "available_tokens": available,
            "failed_tokens": failed,
            "current_index": self.current_index,
            "current_token": self.get_current_token()[:10] + "..."
            if self.get_current_token()
            else None,
        }


# Глобальный экземпляр
_token_rotator = None


def get_token_rotator() -> TokenRotator:
    """
    Получить глобальный экземпляр ротатора токенов.

    Реализует паттерн Singleton для обеспечения единого экземпляра
    ротатора токенов во всем приложении.

    Returns:
        TokenRotator: Глобальный экземпляр ротатора токенов.
    """
    global _token_rotator
    if _token_rotator is None:
        _token_rotator = TokenRotator()
    return _token_rotator
