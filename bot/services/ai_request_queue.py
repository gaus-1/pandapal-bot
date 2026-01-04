"""
Очередь для управления одновременными AI запросами.

Ограничивает количество одновременных запросов к Yandex Cloud API
для предотвращения rate limiting и перегрузки системы.

Использует asyncio.Semaphore для контроля параллелизма.
"""

from asyncio import Semaphore
from typing import Any, Callable, TypeVar

from loguru import logger

# Тип для generic функций
T = TypeVar("T")


class AIRequestQueue:
    """
    Очередь для управления одновременными AI запросами.

    Ограничивает количество одновременных запросов к внешним AI сервисам
    (YandexGPT, SpeechKit, Vision) для предотвращения rate limiting.

    Attributes:
        max_concurrent: Максимальное количество одновременных запросов
        semaphore: Semaphore для контроля параллелизма
    """

    def __init__(self, max_concurrent: int = 50):
        """
        Инициализация очереди AI запросов.

        Args:
            max_concurrent: Максимальное количество одновременных запросов
                          (увеличено до 50 для очень высокой нагрузки, было 30)
        """
        self.max_concurrent = max_concurrent
        self.semaphore = Semaphore(max_concurrent)
        logger.info(f"✅ AIRequestQueue инициализирована: max_concurrent={max_concurrent}")

    async def process(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Выполнить AI запрос через очередь.

        Автоматически ограничивает количество одновременных запросов
        для предотвращения перегрузки и rate limiting.

        Args:
            func: Async функция для выполнения (например, ai_service.generate_response)
            *args: Позиционные аргументы для функции
            **kwargs: Именованные аргументы для функции

        Returns:
            Результат выполнения функции

        Example:
            >>> queue = AIRequestQueue(max_concurrent=10)
            >>> response = await queue.process(
            ...     ai_service.generate_response,
            ...     user_message="Привет",
            ...     chat_history=[]
            ... )
        """
        async with self.semaphore:
            try:
                logger.debug(
                    f"🔄 AI запрос в очереди: {func.__name__} "
                    f"(активных: {self.max_concurrent - self.semaphore._value})"
                )
                result = await func(*args, **kwargs)
                logger.debug(f"✅ AI запрос завершен: {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"❌ Ошибка в AI запросе {func.__name__}: {e}")
                raise

    def get_active_count(self) -> int:
        """
        Получить количество активных запросов.

        Returns:
            int: Количество активных запросов
        """
        return self.max_concurrent - self.semaphore._value

    def get_available_slots(self) -> int:
        """
        Получить количество доступных слотов.

        Returns:
            int: Количество доступных слотов для новых запросов
        """
        return self.semaphore._value


# Глобальный экземпляр очереди (Singleton)
_ai_queue: AIRequestQueue | None = None


def get_ai_request_queue(max_concurrent: int = 12) -> AIRequestQueue:
    """
    Получить глобальный экземпляр очереди AI запросов.

    Реализует паттерн Singleton для обеспечения единого экземпляра
    во всем приложении.

    Args:
        max_concurrent: Максимальное количество одновременных запросов
                      (используется только при первом вызове)

    Returns:
        AIRequestQueue: Глобальный экземпляр очереди
    """
    global _ai_queue
    if _ai_queue is None:
        _ai_queue = AIRequestQueue(max_concurrent=max_concurrent)
    return _ai_queue
