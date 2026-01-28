"""
Comprehensive tests for Cache Service
"""

import asyncio
from unittest.mock import Mock, patch

import pytest

from bot.services.cache_service import CacheService, MemoryCache


class TestMemoryCache:

    @pytest.fixture
    def cache(self):
        return MemoryCache()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_memory_cache_init(self, cache):
        assert cache is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        await cache.set("key1", "value1", ttl=60)
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete(self, cache):
        await cache.set("key1", "value1")
        await cache.delete("key1")
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_clear(self, cache):
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache):
        await cache.set("ttl_key", "ttl_value", ttl=1)
        assert await cache.get("ttl_key") == "ttl_value"
        await asyncio.sleep(2)
        assert await cache.get("ttl_key") is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_complex_data(self, cache):
        data = {"user": "test", "age": 10, "items": [1, 2, 3]}
        await cache.set("complex", data)
        result = await cache.get("complex")
        assert result == data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_stats(self, cache):
        await cache.set("k1", "v1")
        await cache.set("k2", "v2")
        stats = await cache.get_stats()
        assert "total_items" in stats
        assert stats["total_items"] == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_overwrite(self, cache):
        await cache.set("key", "value1")
        await cache.set("key", "value2")
        result = await cache.get("key")
        assert result == "value2"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_multiple_operations(self, cache):
        for i in range(100):
            await cache.set(f"key_{i}", f"value_{i}")

        assert await cache.get("key_0") == "value_0"
        assert await cache.get("key_50") == "value_50"
        assert await cache.get("key_99") == "value_99"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, cache):
        async def set_op(i):
            await cache.set(f"concurrent_{i}", f"value_{i}")

        await asyncio.gather(*[set_op(i) for i in range(50)])

        results = []
        for i in range(50):
            results.append(await cache.get(f"concurrent_{i}"))

        assert len(results) == 50
        assert all(r == f"value_{i}" for i, r in enumerate(results))
