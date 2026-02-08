"""
In-memory LRU кэш и конфигурация кэширования.

Используется как fallback когда Redis недоступен.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass
class CacheConfig:
    """
    Конфигурация кэширования.

    Attributes:
        default_ttl (int): Время жизни записей по умолчанию в секундах (3600 = 1 час).
        max_memory_mb (int): Максимальный размер кэша в памяти (МБ).
        compression_enabled (bool): Включить сжатие данных для экономии памяти.
        serialization_format (str): Формат сериализации данных (json/pickle).
    """

    default_ttl: int = 3600  # 1 час по умолчанию
    max_memory_mb: int = 100  # Максимум памяти для кэша
    compression_enabled: bool = True
    serialization_format: str = "json"


class MemoryCache:
    """
    In-memory кэш как fallback когда Redis недоступен.

    Реализует простой LRU (Least Recently Used) кэш в оперативной памяти
    с поддержкой TTL и автоматической очисткой устаревших записей.
    """

    def __init__(self, max_size: int = 1000):
        """
        Инициализация in-memory кэша.

        Args:
            max_size (int): Максимальное количество записей в кэше (по умолчанию 1000).
        """
        self._cache: dict[str, dict[str, Any]] = {}
        self._max_size = max_size
        self._access_times: dict[str, datetime] = {}

    async def get(self, key: str) -> Any | None:
        """
        Получить значение из кэша.

        Args:
            key (str): Ключ для поиска в кэше.

        Returns:
            Optional[Any]: Значение из кэша или None если не найдено/истекло.
        """
        if key not in self._cache:
            return None

        cache_item = self._cache[key]

        # Проверяем TTL
        if cache_item.get("expires_at") and datetime.now(UTC) > datetime.fromisoformat(
            cache_item["expires_at"]
        ):
            del self._cache[key]
            del self._access_times[key]
            return None

        # Обновляем время доступа
        self._access_times[key] = datetime.now(UTC)

        return cache_item["value"]

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Установить значение в кэш.

        Args:
            key (str): Ключ для сохранения.
            value (Any): Значение для кэширования (любой сериализуемый тип).
            ttl (Optional[int]): Время жизни в секундах (None = бессрочно).

        Returns:
            bool: True при успешном сохранении.
        """
        # Если кэш переполнен, удаляем старые элементы
        if len(self._cache) >= self._max_size:
            await self._evict_oldest()

        expires_at = None
        if ttl:
            expires_at = (datetime.now(UTC) + timedelta(seconds=ttl)).isoformat()

        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._access_times[key] = datetime.now(UTC)

        return True

    async def delete(self, key: str) -> bool:
        """
        Удалить значение из кэша.

        Args:
            key (str): Ключ для удаления.

        Returns:
            bool: True если ключ был удален, False если не существовал.
        """
        if key in self._cache:
            del self._cache[key]
            del self._access_times[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """
        Проверить существование ключа в кэше.

        Args:
            key (str): Ключ для проверки.

        Returns:
            bool: True если ключ существует и не истек, False иначе.
        """
        if key not in self._cache:
            return False

        # Проверяем TTL
        cache_item = self._cache[key]
        if cache_item.get("expires_at") and datetime.now(UTC) > datetime.fromisoformat(
            cache_item["expires_at"]
        ):
            del self._cache[key]
            del self._access_times[key]
            return False

        return True

    async def clear(self) -> bool:
        """
        Очистить весь кэш.

        Returns:
            bool: Всегда True.
        """
        self._cache.clear()
        self._access_times.clear()
        return True

    async def _evict_oldest(self):
        """
        Удалить самый старый элемент из кэша (LRU eviction).

        Используется при переполнении кэша для освобождения места.
        """
        if not self._access_times:
            return

        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        del self._cache[oldest_key]
        del self._access_times[oldest_key]

    async def get_stats(self) -> dict[str, Any]:
        """
        Получить статистику использования кэша.

        Returns:
            Dict[str, Any]: Словарь со статистикой (размер, истекшие, активные записи).
        """
        now = datetime.now(UTC)
        expired_count = 0

        for item in self._cache.values():
            if item.get("expires_at") and now > datetime.fromisoformat(item["expires_at"]):
                expired_count += 1

        return {
            "total_items": len(self._cache),
            "expired_items": expired_count,
            "max_size": self._max_size,
            "memory_usage_mb": len(str(self._cache)) / 1024 / 1024,
        }
