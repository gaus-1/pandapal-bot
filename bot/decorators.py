"""
Декораторы для улучшения качества кода
Реализация паттернов и принципов ООП
@module bot.decorators
"""

import functools
import time
from typing import Any, Callable, Optional, TypeVar

from loguru import logger

F = TypeVar("F", bound=Callable[..., Any])


def log_execution_time(func: F) -> F:
    """
    Декоратор для логирования времени выполнения
    Реализует принцип единственной ответственности (SRP)

    Args:
        func: Функция для декорирования

    Returns:
        F: Декорированная функция
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time

        logger.info(f"⏱️ {func.__name__} выполнена за {execution_time:.3f}s")
        return result

    return wrapper


def retry_on_exception(max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    Декоратор для повторных попыток при исключениях
    Реализует принцип открытости/закрытости (OCP)

    Args:
        max_attempts: Максимальное количество попыток
        delay: Задержка между попытками
        exceptions: Типы исключений для повтора
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
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

            raise last_exception

        return wrapper

    return decorator


def validate_input(**validators):
    """
    Декоратор для валидации входных параметров
    Реализует принцип единственной ответственности (SRP)

    Args:
        **validators: Словарь валидаторов {параметр: функция_валидации}
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Валидация kwargs
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    if not validator(kwargs[param_name]):
                        raise ValueError(f"❌ Некорректное значение параметра {param_name}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def cache_result(ttl: Optional[int] = None):
    """
    Декоратор для кэширования результатов
    Реализует паттерн Cache-Aside

    Args:
        ttl: Время жизни кэша в секундах
    """

    def decorator(func: F) -> F:
        cache = {}
        cache_times = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Создаем ключ кэша
            cache_key = str(args) + str(sorted(kwargs.items()))

            # Проверяем TTL
            if ttl and cache_key in cache_times:
                if time.time() - cache_times[cache_key] > ttl:
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
        wrapper.clear_cache = lambda: cache.clear()
        return wrapper

    return decorator


def rate_limit(calls_per_minute: int = 60):
    """
    Декоратор для ограничения частоты вызовов
    Реализует принцип единственной ответственности (SRP)

    Args:
        calls_per_minute: Количество вызовов в минуту
    """

    def decorator(func: F) -> F:
        call_times = []

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()

            # Удаляем старые вызовы
            call_times[:] = [t for t in call_times if current_time - t < 60]

            # Проверяем лимит
            if len(call_times) >= calls_per_minute:
                raise RuntimeError(f"❌ Превышен лимит вызовов: {calls_per_minute}/мин")

            call_times.append(current_time)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def security_check(check_function: Callable[[], bool]):
    """
    Декоратор для проверки безопасности
    Реализует принцип единственной ответственности (SRP)

    Args:
        check_function: Функция проверки безопасности
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not check_function():
                raise SecurityError("❌ Проверка безопасности не пройдена")
            return func(*args, **kwargs)

        return wrapper

    return decorator


def deprecated(reason: str = "Функция устарела"):
    """
    Декоратор для пометки устаревших функций
    Реализует принцип открытости/закрытости (OCP)

    Args:
        reason: Причина устаревания
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.warning(f"⚠️ Используется устаревшая функция {func.__name__}: {reason}")
            return func(*args, **kwargs)

        return wrapper

    return decorator


class SecurityError(Exception):
    """Исключение для ошибок безопасности"""

    pass


def singleton(cls):
    """
    Декоратор для реализации паттерна Singleton
    Реализует принцип единственной ответственности (SRP)

    Args:
        cls: Класс для применения Singleton
    """

    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def memoize(func: F) -> F:
    """
    Декоратор для мемоизации функций
    Реализует паттерн Memoization

    Args:
        func: Функция для мемоизации

    Returns:
        F: Мемоизированная функция
    """

    cache = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(sorted(kwargs.items()))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    wrapper.cache_clear = lambda: cache.clear()
    return wrapper
