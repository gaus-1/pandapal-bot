"""
Основной сервис кэширования (Redis + in-memory fallback).

Содержит CacheService, глобальный singleton и декоратор cached.
"""

import asyncio
import hashlib
import json
from typing import Any

from loguru import logger

from bot.config import settings
from bot.services.cache.memory import CacheConfig, MemoryCache

# Попытка импорта Redis
try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("⚠️ redis package не установлен, используется in-memory кэш")


class CacheService:
    """
    Универсальный сервис кэширования
    Поддерживает Redis и fallback на in-memory кэш
    """

    def __init__(self):
        """Инициализация сервиса кэширования."""
        self.config = CacheConfig()
        self._redis_client = None
        self._memory_cache = MemoryCache()
        self._use_redis = False

        # Пытаемся подключиться к Redis
        if REDIS_AVAILABLE:
            self._init_redis()
        else:
            logger.warning("🔧 Используется in-memory кэш (Redis недоступен)")

    def _init_redis(self):
        """Инициализация подключения к Redis"""
        try:
            # Настройки Redis из конфигурации
            redis_url = getattr(settings, "redis_url", "")

            if not redis_url:
                logger.info("REDIS_URL not set, using in-memory cache")
                return

            # Инициализируем Redis клиент
            # Подключение произойдет при первом использовании (lazy connection)
            self._redis_client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            logger.info("✅ Redis клиент создан (подключение произойдет при первом запросе)")

        except Exception as e:
            logger.error(f"❌ Ошибка создания Redis клиента: {e}")
            self._redis_client = None

    async def _ensure_redis_connection(self):
        """Проверка и установка подключения к Redis (ленивая инициализация)"""
        if not self._redis_client:
            return False

        # Если уже проверили и подключение работает - возвращаем True
        if self._use_redis:
            return True

        # Проверяем подключение
        try:
            await self._redis_client.ping()
            self._use_redis = True
            logger.debug("✅ Redis подключен успешно")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis недоступен: {e}, используем in-memory кэш")
            self._use_redis = False
            return False

    async def get(self, key: str) -> Any | None:
        """
        Получить значение из кэша

        Args:
            key: Ключ кэша

        Returns:
            Значение или None если не найдено
        """
        try:
            # Ленивая проверка подключения к Redis
            if self._redis_client and not self._use_redis:
                await self._ensure_redis_connection()

            if self._use_redis and self._redis_client:
                value = await self._redis_client.get(key)
                if value:
                    return json.loads(value)
                return None
            else:
                return await self._memory_cache.get(key)

        except Exception as e:
            logger.error(f"❌ Ошибка получения из кэша {key}: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: int | None = None, serialize: bool = True
    ) -> bool:
        """
        Установить значение в кэш

        Args:
            key: Ключ кэша
            value: Значение для сохранения
            ttl: Время жизни в секундах
            serialize: Нужно ли сериализовать значение

        Returns:
            True если успешно сохранено
        """
        try:
            if ttl is None:
                ttl = self.config.default_ttl

            # Ленивая проверка подключения к Redis
            if self._redis_client and not self._use_redis:
                await self._ensure_redis_connection()

            if self._use_redis and self._redis_client:
                if serialize:
                    value = json.dumps(value, ensure_ascii=False, default=str)

                await self._redis_client.setex(key, ttl, value)
                return True
            else:
                await self._memory_cache.set(key, value, ttl)
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в кэш {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Удалить значение из кэша

        Args:
            key: Ключ кэша

        Returns:
            True если успешно удалено
        """
        try:
            # Ленивая проверка подключения к Redis
            if self._redis_client and not self._use_redis:
                await self._ensure_redis_connection()

            if self._use_redis and self._redis_client:
                result = await self._redis_client.delete(key)
                return bool(result and result > 0)
            else:
                delete_result = await self._memory_cache.delete(key)
                return bool(delete_result)

        except Exception as e:
            logger.error(f"❌ Ошибка удаления из кэша {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Проверить существование ключа в кэше

        Args:
            key: Ключ кэша

        Returns:
            True если ключ существует
        """
        try:
            # Ленивая проверка подключения к Redis
            if self._redis_client and not self._use_redis:
                await self._ensure_redis_connection()

            if self._use_redis and self._redis_client:
                result = await self._redis_client.exists(key)
                return bool(result and result > 0)
            else:
                exists_result = await self._memory_cache.exists(key)
                return bool(exists_result)

        except Exception as e:
            logger.error(f"❌ Ошибка проверки существования ключа {key}: {e}")
            return False

    async def clear(self, pattern: str = "*") -> bool:
        """
        Очистить кэш

        Args:
            pattern: Паттерн для удаления (только для Redis)

        Returns:
            True если успешно очищено
        """
        try:
            # Ленивая проверка подключения к Redis
            if self._redis_client and not self._use_redis:
                await self._ensure_redis_connection()

            if self._use_redis and self._redis_client:
                if pattern == "*":
                    await self._redis_client.flushdb()
                else:
                    keys = await self._redis_client.keys(pattern)
                    if keys:
                        await self._redis_client.delete(*keys)
                return True
            else:
                clear_result = await self._memory_cache.clear()
                return bool(clear_result)

        except Exception as e:
            logger.error(f"❌ Ошибка очистки кэша: {e}")
            return False

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Генерировать ключ кэша из параметров

        Args:
            prefix: Префикс ключа
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы

        Returns:
            Сгенерированный ключ
        """
        # Создаем строку из всех параметров
        key_parts = [prefix]

        for arg in args:
            if isinstance(arg, dict | list):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))

        for key, value in sorted(kwargs.items()):
            if isinstance(value, dict | list):
                key_parts.append(f"{key}:{json.dumps(value, sort_keys=True)}")
            else:
                key_parts.append(f"{key}:{value}")

        key_string = ":".join(key_parts)

        # Создаем хэш для длинных ключей
        if len(key_string) > 250:
            # MD5 используется только для кэширования, не для безопасности
            key_hash = hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()  # noqa: S324
            return f"{prefix}:hash:{key_hash}"

        return key_string

    async def get_or_set(
        self, key: str, fetch_func, ttl: int | None = None, *args, **kwargs
    ) -> Any:
        """
        Получить значение из кэша или установить если не существует

        Args:
            key: Ключ кэша
            fetch_func: Функция для получения значения если не в кэше
            ttl: Время жизни в секундах
            *args: Аргументы для fetch_func
            **kwargs: Именованные аргументы для fetch_func

        Returns:
            Значение из кэша или результат fetch_func
        """
        # Пытаемся получить из кэша
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value

        # Получаем значение через функцию
        try:
            if asyncio.iscoroutinefunction(fetch_func):
                value = await fetch_func(*args, **kwargs)
            else:
                value = fetch_func(*args, **kwargs)

            # Сохраняем в кэш
            await self.set(key, value, ttl)

            return value

        except Exception as e:
            logger.error(f"❌ Ошибка в fetch_func для ключа {key}: {e}")
            raise

    async def get_stats(self) -> dict[str, Any]:
        """
        Получить статистику кэша

        Returns:
            Словарь со статистикой
        """
        try:
            if self._use_redis and self._redis_client:
                info = await self._redis_client.info()
                return {
                    "type": "redis",
                    "connected": True,
                    "used_memory_mb": info.get("used_memory", 0) / 1024 / 1024,
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "hit_rate": self._calculate_hit_rate(info),
                }
            else:
                stats_result = await self._memory_cache.get_stats()
                stats: dict[str, Any] = dict(stats_result) if isinstance(stats_result, dict) else {}
                stats["type"] = "memory"
                stats["connected"] = False
                return stats

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики кэша: {e}")
            return {"type": "unknown", "connected": False, "error": str(e)}

    def _calculate_hit_rate(self, info: dict[str, Any]) -> float:
        """Рассчитать процент попаданий в кэш"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses

        if total == 0:
            return 0.0

        hit_rate = (hits / total) * 100
        return float(hit_rate)

    async def close(self):
        """Закрыть соединения"""
        if self._redis_client:
            await self._redis_client.close()


# Глобальный экземпляр сервиса кэширования
cache_service = CacheService()


# Декоратор для кэширования
def cached(ttl: int = 3600, key_prefix: str = "cache"):
    """
    Декоратор для кэширования результатов функций

    Args:
        ttl: Время жизни в секундах
        key_prefix: Префикс для ключа кэша
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Генерируем ключ кэша
            key = cache_service.generate_key(key_prefix, func.__name__, *args, **kwargs)

            # Пытаемся получить из кэша
            cached_result = await cache_service.get(key)
            if cached_result is not None:
                return cached_result

            # Выполняем функцию
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Сохраняем в кэш
            await cache_service.set(key, result, ttl)

            return result

        return wrapper

    return decorator
