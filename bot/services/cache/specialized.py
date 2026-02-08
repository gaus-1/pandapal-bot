"""
Специализированные кэши для конкретных доменов.

UserCache, ModerationCache, AIResponseCache — обёртки над CacheService
с типизированными методами и настроенными TTL/префиксами.
"""

from typing import Any

from bot.services.cache.service import cache_service


class UserCache:
    """Кэш для пользовательских данных"""

    @staticmethod
    async def get_user(telegram_id: int) -> dict[str, Any] | None:
        """Получить пользователя из кэша"""
        key = cache_service.generate_key("user", telegram_id)
        return await cache_service.get(key)

    @staticmethod
    async def set_user(telegram_id: int, user_data: dict[str, Any], ttl: int = 1800) -> bool:
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
    async def get_moderation_result(content_hash: str) -> dict[str, Any] | None:
        """Получить результат модерации из кэша"""
        key = cache_service.generate_key("moderation", content_hash)
        return await cache_service.get(key)

    @staticmethod
    async def set_moderation_result(
        content_hash: str, result: dict[str, Any], ttl: int = 7200
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
    """Кэш для ответов нейросети"""

    @staticmethod
    async def get_response(query_hash: str) -> str | None:
        """Получить ответ из кэша"""
        key = cache_service.generate_key("ai_response", query_hash)
        return await cache_service.get(key)

    @staticmethod
    async def set_response(query_hash: str, response: str, ttl: int = 3600) -> bool:
        """Сохранить ответ в кэш"""
        key = cache_service.generate_key("ai_response", query_hash)
        return await cache_service.set(key, response, ttl)

    @staticmethod
    async def invalidate_response(query_hash: str) -> bool:
        """Удалить ответ из кэша"""
        key = cache_service.generate_key("ai_response", query_hash)
        return await cache_service.delete(key)
