"""Обратная совместимость — реэкспорт из bot.services.cache."""

from bot.services.cache import (  # noqa: F401
    AIResponseCache,
    CacheConfig,
    CacheService,
    MemoryCache,
    ModerationCache,
    UserCache,
    cache_service,
    cached,
)
