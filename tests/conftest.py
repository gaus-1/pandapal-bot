"""
Pytest конфигурация для PandaPal Bot
Настройка тестового окружения для детского проекта
"""
import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from typing import Generator, AsyncGenerator

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.services.ai_service import GeminiAIService
from bot.services.moderation_service import ContentModerationService
from bot.models import User, ChatHistory


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Создание event loop для async тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_user() -> User:
    """Мок пользователя для тестов"""
    return User(
        telegram_id=123456789,
        username="test_child",
        first_name="Тестовый",
        last_name="Ребенок",
        user_type="child",
        age=10,
        grade=5
    )


@pytest.fixture
def mock_parent_user() -> User:
    """Мок родителя для тестов"""
    return User(
        telegram_id=987654321,
        username="test_parent",
        first_name="Тестовый",
        last_name="Родитель",
        user_type="parent",
        age=35,
        grade=None
    )


@pytest.fixture
def mock_teacher_user() -> User:
    """Мок учителя для тестов"""
    return User(
        telegram_id=456789123,
        username="test_teacher",
        first_name="Тестовый",
        last_name="Учитель",
        user_type="teacher",
        age=30,
        grade=None
    )


@pytest.fixture
def mock_ai_service() -> Mock:
    """Мок AI сервиса"""
    service = Mock(spec=GeminiAIService)
    service.generate_response = AsyncMock(return_value="Тестовый ответ AI")
    service.analyze_sentiment = AsyncMock(return_value="positive")
    service.check_content_safety = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_security_service() -> Mock:
    """Мок сервиса модерации"""
    service = Mock(spec=ContentModerationService)
    service.check_message_safety = AsyncMock(return_value=True)
    service.filter_inappropriate_content = AsyncMock(return_value="Очищенное сообщение")
    service.log_security_event = AsyncMock()
    return service


@pytest.fixture
def mock_chat_history() -> ChatHistory:
    """Мок истории чата"""
    return ChatHistory(
        user_id=123456789,
        message="Тестовое сообщение",
        response="Тестовый ответ",
        timestamp="2024-01-01 12:00:00",
        message_type="text",
        sentiment="positive"
    )


# Маркеры для категоризации тестов
def pytest_configure(config):
    """Настройка маркеров pytest"""
    config.addinivalue_line("markers", "unit: Unit тесты")
    config.addinivalue_line("markers", "integration: Integration тесты")
    config.addinivalue_line("markers", "security: Тесты безопасности")
    config.addinivalue_line("markers", "performance: Тесты производительности")
    config.addinivalue_line("markers", "child_safety: Тесты безопасности детей")
    config.addinivalue_line("markers", "slow: Медленные тесты")