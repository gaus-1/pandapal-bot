"""
Пакет кэширования — Redis с fallback на in-memory LRU кэш.

Публичный API:
    CacheConfig, MemoryCache  — конфигурация и in-memory реализация
    CacheService, cache_service, cached  — основной сервис и декоратор
    UserCache, ModerationCache, AIResponseCache  — специализированные кэши
"""

from bot.services.cache.memory import CacheConfig, MemoryCache  # noqa: F401
from bot.services.cache.service import CacheService, cache_service, cached  # noqa: F401
from bot.services.cache.specialized import (  # noqa: F401
    AIResponseCache,
    ModerationCache,
    UserCache,
)

__all__ = [
    "CacheConfig",
    "MemoryCache",
    "CacheService",
    "cache_service",
    "cached",
    "UserCache",
    "ModerationCache",
    "AIResponseCache",
]
