"""
Circuit Breaker для внешних сервисов.

Отслеживает ошибки и временно блокирует запросы при массовых сбоях,
возвращая быстрый fallback вместо долгих таймаутов.

Состояния:
- CLOSED: нормальная работа, запросы проходят
- OPEN: сервис недоступен, запросы блокируются (быстрый fallback)
- HALF_OPEN: пробный запрос для проверки восстановления
"""

import asyncio
import functools
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

from loguru import logger


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit Breaker для защиты от каскадных сбоев внешних сервисов."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
    ):
        """
        Инициализация Circuit Breaker.

        Args:
            name: Имя сервиса (для логов)
            failure_threshold: Кол-во ошибок подряд для перехода в OPEN
            recovery_timeout: Секунд в OPEN до перехода в HALF_OPEN
            half_open_max_calls: Кол-во пробных запросов в HALF_OPEN
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Текущее состояние с автопереходом OPEN -> HALF_OPEN."""
        if (
            self._state == CircuitState.OPEN
            and time.monotonic() - self._last_failure_time >= self.recovery_timeout
        ):
            self._state = CircuitState.HALF_OPEN
            self._half_open_calls = 0
            logger.info(
                f"🔄 CircuitBreaker [{self.name}]: OPEN -> HALF_OPEN " f"(попытка восстановления)"
            )
        return self._state

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Выполнить вызов через Circuit Breaker.

        Args:
            func: Асинхронная функция
            *args, **kwargs: Аргументы функции

        Returns:
            Результат функции

        Raises:
            CircuitOpenError: Если цепь разомкнута
        """
        async with self._lock:
            current_state = self.state

            if current_state == CircuitState.OPEN:
                raise CircuitOpenError(
                    f"CircuitBreaker [{self.name}] OPEN: "
                    f"сервис временно недоступен, повторите через "
                    f"{int(self.recovery_timeout - (time.monotonic() - self._last_failure_time))}с"
                )

            if current_state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitOpenError(
                        f"CircuitBreaker [{self.name}] HALF_OPEN: " f"пробные запросы исчерпаны"
                    )
                self._half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure(e)
            raise

    async def _on_success(self) -> None:
        """Обработка успешного вызова."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(
                    f"✅ CircuitBreaker [{self.name}]: HALF_OPEN -> CLOSED "
                    f"(сервис восстановлен)"
                )
            self._state = CircuitState.CLOSED
            self._failure_count = 0

    async def _on_failure(self, error: Exception) -> None:
        """Обработка ошибки."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"⚠️ CircuitBreaker [{self.name}]: HALF_OPEN -> OPEN "
                    f"(пробный запрос провалился: {error})"
                )
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"⚠️ CircuitBreaker [{self.name}]: CLOSED -> OPEN "
                    f"({self._failure_count} ошибок подряд: {error})"
                )


class CircuitOpenError(Exception):
    """Исключение: Circuit Breaker разомкнут."""

    pass


def with_circuit_breaker(
    circuit: CircuitBreaker,
    fallback_message: str = "Сервис временно недоступен. Попробуй через минуту.",
):
    """
    Декоратор: оборачивает async-функцию в Circuit Breaker с fallback.

    Args:
        circuit: Экземпляр CircuitBreaker
        fallback_message: Сообщение при разомкнутой цепи
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await circuit.call(func, *args, **kwargs)
            except CircuitOpenError:
                logger.warning(
                    f"⚡ CircuitBreaker [{circuit.name}]: быстрый fallback " f"для {func.__name__}"
                )
                return fallback_message

        return wrapper

    return decorator


# Глобальные Circuit Breaker для Yandex Cloud
yandex_gpt_circuit = CircuitBreaker(
    name="YandexGPT",
    failure_threshold=5,
    recovery_timeout=30.0,
)

yandex_stt_circuit = CircuitBreaker(
    name="SpeechKit",
    failure_threshold=3,
    recovery_timeout=45.0,
)

yandex_vision_circuit = CircuitBreaker(
    name="Vision",
    failure_threshold=3,
    recovery_timeout=45.0,
)
