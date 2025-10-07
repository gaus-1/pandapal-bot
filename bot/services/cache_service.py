"""
Сервис кэширования для оптимизации производительности
Использует Redis для быстрого доступа к часто используемым данным

"""

import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger

# Redis imports закомментированы - используем только in-memory cache
REDIS_AVAILABLE = False

from bot.config import settings


@dataclass
class CacheConfig:
    """Конфигурация кэширования"""

    default_ttl: int = 3600  # 1 час по умолчанию
    max_memory_mb: int = 100  # Максимум памяти для кэша
    compression_enabled: bool = True
    serialization_format: str = "json"


class MemoryCache:
    """In-memory кэш как fallback когда Redis недоступен"""

    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._access_times: Dict[str, datetime] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        if key not in self._cache:
            return None

        cache_item = self._cache[key]

        # Проверяем TTL
        if cache_item.get("expires_at"):
            if datetime.utcnow() > datetime.fromisoformat(cache_item["expires_at"]):
                del self._cache[key]
                del self._access_times[key]
                return None

        # Обновляем время доступа
        self._access_times[key] = datetime.utcnow()

        return cache_item["value"]

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Установить значение в кэш"""
        # Если кэш переполнен, удаляем старые элементы
        if len(self._cache) >= self._max_size:
            await self._evict_oldest()

        expires_at = None
        if ttl:
            expires_at = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()

        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._access_times[key] = datetime.utcnow()

        return True

    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        if key in self._cache:
            del self._cache[key]
            del self._access_times[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        if key not in self._cache:
            return False

        # Проверяем TTL
        cache_item = self._cache[key]
        if cache_item.get("expires_at"):
            if datetime.utcnow() > datetime.fromisoformat(cache_item["expires_at"]):
                del self._cache[key]
                del self._access_times[key]
                return False

        return True

    async def clear(self) -> bool:
        """Очистить весь кэш"""
        self._cache.clear()
        self._access_times.clear()
        return True

    async def _evict_oldest(self):
        """Удалить самый старый элемент"""
        if not self._access_times:
            return

        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        del self._cache[oldest_key]
        del self._access_times[oldest_key]

    async def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        now = datetime.utcnow()
        expired_count = 0

        for item in self._cache.values():
            if item.get("expires_at"):
                if now > datetime.fromisoformat(item["expires_at"]):
                    expired_count += 1

        return {
            "total_items": len(self._cache),
            "expired_items": expired_count,
            "max_size": self._max_size,
            "memory_usage_mb": len(str(self._cache)) / 1024 / 1024,
        }


class CacheService:
    """
    Универсальный сервис кэширования
    Поддерживает Redis и fallback на in-memory кэш
    """

    def __init__(self):
        self.config = CacheConfig()
        self._redis_client: Optional[aioredis.Redis] = None
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
            redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")

            self._redis_client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Проверяем подключение (синхронно для инициализации)
            # asyncio.create_task(self._test_redis_connection())

        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Redis: {e}")
            self._redis_client = None

    async def _test_redis_connection(self):
        """Тестирование подключения к Redis"""
        try:
            if self._redis_client:
                await self._redis_client.ping()
                self._use_redis = True
                logger.info("✅ Redis подключен успешно")
        except Exception as e:
            logger.error(f"❌ Redis недоступен: {e}")
            self._use_redis = False
            self._redis_client = None

    async def get(self, key: str) -> Optional[Any]:
        """
        Получить значение из кэша

        Args:
            key: Ключ кэша

        Returns:
            Значение или None если не найдено
        """
        try:
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
        self, key: str, value: Any, ttl: Optional[int] = None, serialize: bool = True
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
            if self._use_redis and self._redis_client:
                result = await self._redis_client.delete(key)
                return result > 0
            else:
                return await self._memory_cache.delete(key)

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
            if self._use_redis and self._redis_client:
                result = await self._redis_client.exists(key)
                return result > 0
            else:
                return await self._memory_cache.exists(key)

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
            if self._use_redis and self._redis_client:
                if pattern == "*":
                    await self._redis_client.flushdb()
                else:
                    keys = await self._redis_client.keys(pattern)
                    if keys:
                        await self._redis_client.delete(*keys)
                return True
            else:
                return await self._memory_cache.clear()

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
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))

        for key, value in sorted(kwargs.items()):
            if isinstance(value, (dict, list)):
                key_parts.append(f"{key}:{json.dumps(value, sort_keys=True)}")
            else:
                key_parts.append(f"{key}:{value}")

        key_string = ":".join(key_parts)

        # Создаем хэш для длинных ключей
        if len(key_string) > 250:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"

        return key_string

    async def get_or_set(
        self, key: str, fetch_func, ttl: Optional[int] = None, *args, **kwargs
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

    async def get_stats(self) -> Dict[str, Any]:
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
                stats = await self._memory_cache.get_stats()
                stats["type"] = "memory"
                stats["connected"] = False
                return stats

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики кэша: {e}")
            return {"type": "unknown", "connected": False, "error": str(e)}

    def _calculate_hit_rate(self, info: Dict[str, Any]) -> float:
        """Рассчитать процент попаданий в кэш"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses

        if total == 0:
            return 0.0

        return (hits / total) * 100

    async def close(self):
        """Закрыть соединения"""
        if self._redis_client:
            await self._redis_client.close()


# Глобальный экземпляр сервиса кэширования
cache_service = CacheService()


# Декораторы для кэширования
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


# Специализированные методы кэширования
class UserCache:
    """Кэш для пользовательских данных"""

    @staticmethod
    async def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя из кэша"""
        key = cache_service.generate_key("user", telegram_id)
        return await cache_service.get(key)

    @staticmethod
    async def set_user(telegram_id: int, user_data: Dict[str, Any], ttl: int = 1800) -> bool:
        """Сохранить пользователя в кэш"""
        key = cache_service.generate_key("user", telegram_id)
        return await cache_service.set(key, user_data, ttl)

    @staticmethod
    async def invalidate_user(telegram_id: int) -> bool:
        """Удалить пользователя из кэша"""
        key = cache_service.generate_key("user", telegram_id)
        return await cache_service.delete(key)


class ModerationCache:
    """Кэш для результатов модерации"""

    @staticmethod
    async def get_moderation_result(content_hash: str) -> Optional[Dict[str, Any]]:
        """Получить результат модерации из кэша"""
        key = cache_service.generate_key("moderation", content_hash)
        return await cache_service.get(key)

    @staticmethod
    async def set_moderation_result(
        content_hash: str, result: Dict[str, Any], ttl: int = 7200
    ) -> bool:
        """Сохранить результат модерации в кэш"""
        key = cache_service.generate_key("moderation", content_hash)
        return await cache_service.set(key, result, ttl)

    @staticmethod
    async def invalidate_moderation(content_hash: str) -> bool:
        """Удалить результат модерации из кэша"""
        key = cache_service.generate_key("moderation", content_hash)
        return await cache_service.delete(key)


class AIResponseCache:
    """Кэш для ответов AI"""

    @staticmethod
    async def get_response(query_hash: str) -> Optional[str]:
        """Получить ответ AI из кэша"""
        key = cache_service.generate_key("ai_response", query_hash)
        return await cache_service.get(key)

    @staticmethod
    async def set_response(query_hash: str, response: str, ttl: int = 3600) -> bool:
        """Сохранить ответ AI в кэш"""
        key = cache_service.generate_key("ai_response", query_hash)
        return await cache_service.set(key, response, ttl)

    @staticmethod
    async def invalidate_response(query_hash: str) -> bool:
        """Удалить ответ AI из кэша"""
        key = cache_service.generate_key("ai_response", query_hash)
        return await cache_service.delete(key)
