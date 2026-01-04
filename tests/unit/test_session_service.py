"""
Тесты для SessionService (управление сессиями).

Проверяет:
- Создание сессий
- Получение сессий
- Удаление сессий
- TTL и автоочистку
- Fallback на in-memory при недоступности Redis
"""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from bot.services.session_service import SessionService, get_session_service


@pytest.fixture
def mock_settings_no_redis(monkeypatch):
    """Mock настроек БЕЗ Redis."""
    monkeypatch.setattr("bot.config.settings.redis_url", "")


@pytest.fixture
def mock_settings_with_redis(monkeypatch):
    """Mock настроек С Redis."""
    monkeypatch.setattr("bot.config.settings.redis_url", "redis://localhost:6379")


@pytest.fixture
def session_service_memory():
    """SessionService с in-memory хранилищем."""
    with patch("bot.services.session_service.REDIS_AVAILABLE", False):
        service = SessionService()
        yield service


@pytest_asyncio.fixture
async def session_service_redis():
    """SessionService с mock Redis."""
    mock_redis = AsyncMock()
    mock_redis.setex = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.keys = AsyncMock(return_value=[])
    mock_redis.close = AsyncMock()

    with patch("bot.services.session_service.REDIS_AVAILABLE", True):
        with patch("bot.services.session_service.aioredis.from_url", return_value=mock_redis):
            service = SessionService()
            service._use_redis = True
            service._redis_client = mock_redis
            yield service
            await service.close()


class TestSessionServiceMemory:
    """Тесты для in-memory хранилища сессий."""

    @pytest.mark.asyncio
    async def test_create_session_memory(self, session_service_memory):
        """Тест создания сессии в памяти."""
        user_data = {
            "telegram_id": 123456,
            "full_name": "Test User",
            "is_premium": False,
        }

        token = await session_service_memory.create_session(123456, user_data)

        assert token is not None
        assert len(token) > 20  # token_urlsafe(32) → длинная строка

        # Проверяем что сессия создана
        session = await session_service_memory.get_session(token)
        assert session is not None
        assert session.telegram_id == 123456
        assert session.user_data == user_data

    @pytest.mark.asyncio
    async def test_get_session_memory_not_found(self, session_service_memory):
        """Тест получения несуществующей сессии."""
        session = await session_service_memory.get_session("nonexistent_token")
        assert session is None

    @pytest.mark.asyncio
    async def test_delete_session_memory(self, session_service_memory):
        """Тест удаления сессии из памяти."""
        user_data = {"telegram_id": 123456, "full_name": "Test User"}
        token = await session_service_memory.create_session(123456, user_data)

        # Проверяем что сессия существует
        session = await session_service_memory.get_session(token)
        assert session is not None

        # Удаляем
        result = await session_service_memory.delete_session(token)
        assert result is True

        # Проверяем что сессия удалена
        session = await session_service_memory.get_session(token)
        assert session is None

    @pytest.mark.asyncio
    async def test_session_expiration_memory(self, session_service_memory):
        """Тест истечения срока действия сессии."""
        user_data = {"telegram_id": 123456, "full_name": "Test User"}
        token = await session_service_memory.create_session(123456, user_data)

        # Получаем сессию и меняем expires_at на прошлое
        session = session_service_memory._memory_sessions[token]
        session.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)

        # Проверяем что сессия считается истёкшей
        expired_session = await session_service_memory.get_session(token)
        assert expired_session is None

    @pytest.mark.asyncio
    async def test_refresh_session_memory(self, session_service_memory):
        """Тест продления сессии."""
        user_data = {"telegram_id": 123456, "full_name": "Test User"}
        token = await session_service_memory.create_session(123456, user_data)

        # Получаем текущий expires_at
        session_before = session_service_memory._memory_sessions[token]
        expires_before = session_before.expires_at

        # Продлеваем
        result = await session_service_memory.refresh_session(token)
        assert result is True

        # Проверяем что expires_at обновился
        session_after = session_service_memory._memory_sessions[token]
        expires_after = session_after.expires_at

        assert expires_after > expires_before

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_memory(self, session_service_memory):
        """Тест автоочистки истёкших сессий."""
        # Создаём несколько сессий
        tokens = []
        for i in range(3):
            user_data = {"telegram_id": 123456 + i, "full_name": f"User {i}"}
            token = await session_service_memory.create_session(123456 + i, user_data)
            tokens.append(token)

        # Делаем первую сессию истёкшей
        session_service_memory._memory_sessions[tokens[0]].expires_at = datetime.now(
            timezone.utc
        ).replace(tzinfo=None) - timedelta(days=1)

        # Вызываем очистку
        session_service_memory._cleanup_memory()

        # Проверяем что истёкшая сессия удалена
        assert tokens[0] not in session_service_memory._memory_sessions
        # А остальные остались
        assert tokens[1] in session_service_memory._memory_sessions
        assert tokens[2] in session_service_memory._memory_sessions

    @pytest.mark.asyncio
    async def test_get_stats_memory(self, session_service_memory):
        """Тест получения статистики (in-memory)."""
        # Создаём сессии
        for i in range(5):
            user_data = {"telegram_id": 123456 + i, "full_name": f"User {i}"}
            await session_service_memory.create_session(123456 + i, user_data)

        stats = await session_service_memory.get_stats()

        assert stats["storage"] == "memory"
        assert stats["total_sessions"] == 5
        assert stats["redis_connected"] is False


class TestSessionServiceRedis:
    """Тесты для Redis хранилища сессий."""

    @pytest.mark.asyncio
    async def test_create_session_redis(self, session_service_redis):
        """Тест создания сессии в Redis."""
        user_data = {
            "telegram_id": 123456,
            "full_name": "Test User",
            "is_premium": True,
        }

        token = await session_service_redis.create_session(123456, user_data)

        assert token is not None
        # Проверяем что setex был вызван
        session_service_redis._redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_redis(self, session_service_redis):
        """Тест получения сессии из Redis."""
        import json

        # Mock возвращает данные сессии
        session_data = {
            "telegram_id": 123456,
            "user_data": {"telegram_id": 123456, "full_name": "Test User"},
            "expires_at": (
                datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)
            ).isoformat(),
        }
        session_service_redis._redis_client.get.return_value = json.dumps(session_data)

        session = await session_service_redis.get_session("test_token")

        assert session is not None
        assert session.telegram_id == 123456

    @pytest.mark.asyncio
    async def test_delete_session_redis(self, session_service_redis):
        """Тест удаления сессии из Redis."""
        result = await session_service_redis.delete_session("test_token")

        assert result is True
        session_service_redis._redis_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stats_redis(self, session_service_redis):
        """Тест получения статистики (Redis)."""
        # Mock возвращает 3 ключа
        session_service_redis._redis_client.keys.return_value = [
            "session:token1",
            "session:token2",
            "session:token3",
        ]

        stats = await session_service_redis.get_stats()

        assert stats["storage"] == "redis"
        assert stats["total_sessions"] == 3
        assert stats["redis_connected"] is True


class TestSessionServiceSingleton:
    """Тесты для singleton паттерна."""

    def test_get_session_service_singleton(self):
        """Тест что get_session_service возвращает один экземпляр."""
        service1 = get_session_service()
        service2 = get_session_service()

        assert service1 is service2


class TestSessionServiceFallback:
    """Тесты для fallback механизма (Redis → in-memory)."""

    @pytest.mark.asyncio
    async def test_fallback_on_redis_error(self, session_service_redis):
        """Тест fallback на in-memory при ошибке Redis."""
        # Симулируем ошибку Redis
        session_service_redis._redis_client.setex.side_effect = Exception("Redis unavailable")

        user_data = {"telegram_id": 123456, "full_name": "Test User"}

        # Создаём сессию (должен быть fallback на memory)
        token = await session_service_redis.create_session(123456, user_data)

        assert token is not None
        # Проверяем что сессия сохранена в памяти
        assert token in session_service_redis._memory_sessions
