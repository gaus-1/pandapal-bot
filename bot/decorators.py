"""Декораторы для улучшения качества кода."""

import functools
import time
from collections.abc import Callable
from typing import Any

from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


def async_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exceptions: tuple = (Exception,),
):
    """Асинхронный декоратор retry с экспоненциальной задержкой."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=lambda retry_state: logger.warning(
            f"🔄 Retry {retry_state.attempt_number}/{max_attempts} "
            f"после ошибки: {retry_state.outcome.exception()}"
        ),
    )


def log_execution_time[F: Callable[..., Any]](func: F) -> F:
    """Декоратор для логирования времени выполнения функции."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time

        logger.info(f"⏱️ {func.__name__} выполнена за {execution_time:.3f}s")
        return result

    return wrapper  # type: ignore[return-value]


def retry_on_exception[F: Callable[..., Any]](
    max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)
):
    """Декоратор для автоматических повторных попыток при возникновении исключений."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"🔄 {func.__name__} попытка {attempt + 1} "
                            f"неудачна: {e}. Повтор через {delay}s"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"❌ {func.__name__} все попытки исчерпаны: {e}")

            raise last_exception  # type: ignore

        return wrapper  # type: ignore[return-value]

    return decorator


def validate_input[F: Callable[..., Any]](**validators):
    """Декоратор для валидации входных параметров."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore
            # Валидация kwargs
            for param_name, validator in validators.items():
                if param_name in kwargs and not validator(kwargs[param_name]):
                    raise ValueError(f"❌ Некорректное значение параметра {param_name}")

            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def cache_result[F: Callable[..., Any]](ttl: int | None = None):
    """Декоратор для кэширования результатов."""

    def decorator(func: F) -> F:
        cache: dict[str, Any] = {}
        cache_times: dict[str, float] = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore
            # Создаем ключ кэша
            cache_key = str(args) + str(sorted(kwargs.items()))

            # Проверяем TTL
            if ttl and cache_key in cache_times and time.time() - cache_times[cache_key] > ttl:
                del cache[cache_key]
                del cache_times[cache_key]

            # Возвращаем из кэша или вычисляем
            if cache_key in cache:
                logger.debug(f"💾 Кэш попадание для {func.__name__}")
                return cache[cache_key]

            result = func(*args, **kwargs)
            cache[cache_key] = result
            cache_times[cache_key] = time.time()

            logger.debug(f"💾 Кэш обновлен для {func.__name__}")
            return result

        # Добавляем метод очистки кэша
        wrapper.clear_cache = lambda: cache.clear()  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator


def rate_limit[F: Callable[..., Any]](calls_per_minute: int = 60):
    """Декоратор для ограничения частоты вызовов."""

    def decorator(func: F) -> F:
        call_times: list[float] = []

        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore
            current_time = time.time()

            # Удаляем старые вызовы
            call_times[:] = [t for t in call_times if current_time - t < 60]

            # Проверяем лимит
            if len(call_times) >= calls_per_minute:
                raise RuntimeError(f"❌ Превышен лимит вызовов: {calls_per_minute}/мин")

            call_times.append(current_time)
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def security_check[F: Callable[..., Any]](check_function: Callable[[], bool]):
    """Декоратор для проверки безопасности."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore
            if not check_function():
                raise SecurityError("❌ Проверка безопасности не пройдена")
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def deprecated[F: Callable[..., Any]](reason: str = "Функция устарела"):
    """Декоратор для пометки устаревших функций."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore
            logger.warning(f"⚠️ Используется устаревшая функция {func.__name__}: {reason}")
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


class SecurityError(Exception):
    """Исключение для ошибок безопасности"""

    pass


def singleton(cls):
    """Декоратор для реализации паттерна Singleton."""
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def memoize[F: Callable[..., Any]](func: F) -> F:
    """Кэширование без TTL. Алиас для cache_result()."""
    return cache_result()(func)
