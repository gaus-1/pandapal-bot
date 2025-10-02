"""
Конфигурация pytest
Фикстуры и настройки для всех тестов
@module tests.conftest
"""

import os
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from bot.models import Base
from bot.config import settings
from bot.services.user_service import UserService
from bot.services.moderation_service import ContentModerationService
from bot.services.ai_service import GeminiAIService
from bot.services.history_service import ChatHistoryService


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для асинхронных тестов"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db():
    """Создание тестовой базы данных в памяти"""
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def mock_user():
    """Мок пользователя"""
    return Mock(
        telegram_id=12345,
        username="testuser",
        first_name="Test",
        last_name="User",
        age=12,
        grade=6,
        is_active=True
    )


@pytest.fixture
def mock_telegram_user():
    """Мок Telegram пользователя"""
    return Mock(
        id=12345,
        username="testuser",
        first_name="Test",
        last_name="User"
    )


@pytest.fixture
def user_service(test_db):
    """Сервис пользователей для тестов"""
    return UserService(test_db)


@pytest.fixture
def moderation_service():
    """Сервис модерации для тестов"""
    return ContentModerationService()


@pytest.fixture
def ai_service():
    """Сервис ИИ для тестов"""
    service = GeminiAIService()
    # Мокаем реальные API вызовы
    service.generate_content = AsyncMock(return_value=Mock(text="Test response"))
    return service


@pytest.fixture
def history_service(test_db):
    """Сервис истории чата для тестов"""
    return ChatHistoryService(test_db)


@pytest.fixture
def mock_ai_response():
    """Мок ответа ИИ"""
    response = Mock()
    response.text = "Это тестовый ответ от ИИ"
    return response


@pytest.fixture
def sample_chat_history():
    """Образец истории чата"""
    return [
        {"role": "user", "content": "Привет!"},
        {"role": "assistant", "content": "Привет! Как дела?"},
        {"role": "user", "content": "Хорошо, спасибо!"}
    ]


@pytest.fixture
def forbidden_content_samples():
    """Образцы запрещенного контента"""
    return [
        "Расскажи про наркотики",
        "Как сделать оружие",
        "Политические партии",
        "Взрослый контент",
        "Нецензурная лексика"
    ]


@pytest.fixture
def safe_content_samples():
    """Образцы безопасного контента"""
    return [
        "Привет! Как дела?",
        "Расскажи про историю России",
        "Помоги решить задачу по математике",
        "Что такое фотосинтез?",
        "Объясни правило деления"
    ]


@pytest.fixture
def mock_telegram_message():
    """Мок Telegram сообщения"""
    return Mock(
        from_user=Mock(
            id=12345,
            username="testuser",
            first_name="Test",
            last_name="User"
        ),
        text="Тестовое сообщение",
        chat=Mock(id=12345),
        message_id=1
    )


@pytest.fixture
def mock_bot():
    """Мок Telegram бота"""
    bot = AsyncMock()
    bot.send_chat_action = AsyncMock()
    bot.send_message = AsyncMock()
    bot.answer = AsyncMock()
    return bot


@pytest.fixture(autouse=True)
def setup_test_env():
    """Настройка тестового окружения"""
    # Устанавливаем тестовые переменные окружения
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
    os.environ["GEMINI_API_KEY"] = "test_api_key"
    os.environ["CONTENT_FILTER_LEVEL"] = "3"
    os.environ["DEBUG"] = "True"
    
    yield
    
    # Очистка после тестов
    for key in ["DATABASE_URL", "TELEGRAM_BOT_TOKEN", "GEMINI_API_KEY", "CONTENT_FILTER_LEVEL", "DEBUG"]:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def mock_logger():
    """Мок логгера"""
    return Mock()


# Маркеры для группировки тестов
def pytest_configure(config):
    """Конфигурация pytest маркеров"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "ai: AI service tests")
    config.addinivalue_line("markers", "database: Database tests")
    config.addinivalue_line("markers", "moderation: Moderation tests")
