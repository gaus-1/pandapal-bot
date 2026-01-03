"""
Тесты для bot/handlers/ai_chat.py
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.unit
class TestAIChatHandler:
    """Тесты для обработчика AI чата"""

    @pytest.fixture
    def mock_message(self):
        """Мок сообщения"""
        message = MagicMock()
        message.from_user.id = 123456789
        message.from_user.username = "test_user"
        message.from_user.first_name = "Тест"
        message.from_user.last_name = "Пользователь"
        message.text = "Привет, как дела?"
        message.chat.id = 123456789
        message.answer = AsyncMock()
        message.bot.send_chat_action = AsyncMock()
        return message

    @pytest.fixture
    def mock_state(self):
        """Мок FSM состояния"""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_start_ai_chat(self, mock_message, mock_state):
        """Тест активации режима AI чата - без моков внутренних компонентов"""
        from bot.handlers.ai_chat import start_ai_chat

        mock_message.text = "💬 Общение с AI"

        await start_ai_chat(mock_message, mock_state)

        # Проверяем результат работы, а не факт вызова методов
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        if call_args:
            answer_text = ""
            if call_args[0]:
                answer_text = call_args[0][0]
            elif call_args[1] and "text" in call_args[1]:
                answer_text = call_args[1]["text"]
            assert "Режим общения с AI" in answer_text or "AI" in answer_text

    @pytest.mark.asyncio
    @patch("bot.handlers.ai_chat.get_ai_service")  # Мокаем только внешний AI API
    async def test_handle_ai_message_safe_content_real_services(
        self, mock_get_ai, mock_message, mock_state
    ):
        """Тест обработки безопасного сообщения с РЕАЛЬНЫМИ сервисами"""
        import os
        import tempfile

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from bot.database import get_db
        from bot.handlers.ai_chat import handle_ai_message
        from bot.models import Base

        # Создаем РЕАЛЬНУЮ БД для теста
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)

        # Мокаем только внешний AI API (Yandex GPT)
        mock_ai_service = MagicMock()
        mock_ai_service.generate_response = AsyncMock(
            return_value="AI ответ на вопрос про математику"
        )
        mock_get_ai.return_value = mock_ai_service

        # Используем РЕАЛЬНЫЙ get_db с реальной БД
        real_session = SessionLocal()

        # Создаем реального пользователя через реальный сервис
        from bot.services.user_service import UserService

        user_service = UserService(real_session)
        user = user_service.get_or_create_user(
            telegram_id=123456789, username="test_user", first_name="Тест", last_name="Пользователь"
        )
        user_service.update_user_profile(telegram_id=123456789, age=10, user_type="child")
        real_session.commit()

        def mock_get_db_real():
            return real_session

        try:
            with patch("bot.handlers.ai_chat.get_db", side_effect=lambda: mock_get_db_real()):
                await handle_ai_message(mock_message, mock_state)

            # Проверяем результат работы - может быть несколько вызовов (достижение + ответ AI)
            assert mock_message.answer.call_count >= 1, "Должен быть хотя бы один ответ"
            
            # Проверяем что последний вызов содержит ответ
            last_call = mock_message.answer.call_args_list[-1]
            if last_call:
                answer_text = ""
                if last_call[0]:
                    answer_text = last_call[0][0] if last_call[0] else ""
                elif last_call[1] and "text" in last_call[1]:
                    answer_text = last_call[1]["text"]
                assert len(answer_text) > 0  # Проверяем результат, а не реализацию
        finally:
            real_session.close()
            engine.dispose()
            os.close(db_fd)
            os.unlink(db_path)

    def test_handle_ai_message_unsafe_content_real_moderation(self, mock_message, mock_state):
        """Тест обработки небезопасного сообщения с РЕАЛЬНОЙ модерацией"""
        # Используем РЕАЛЬНЫЙ сервис модерации, не мок
        from bot.services.moderation_service import ContentModerationService

        moderation = ContentModerationService()
        mock_message.text = "наркотики"

        # Проверяем реальную модерацию
        is_safe, reason = moderation.is_safe_content(mock_message.text)
        assert is_safe is False
        assert reason is not None

        # Проверяем что есть безопасный альтернативный ответ
        safe_response = moderation.get_safe_response_alternative("blocked_content")
        assert safe_response is not None
        assert len(safe_response) > 0

        # Проверяем что альтернативный ответ безопасен
        is_safe_response, _ = moderation.is_safe_content(safe_response)
        assert is_safe_response is True

    @pytest.mark.asyncio
    @patch("bot.handlers.ai_chat.get_ai_service")  # Мокаем только внешний AI API
    async def test_handle_ai_message_error_real_services(
        self, mock_get_ai, mock_message, mock_state
    ):
        """Тест обработки ошибки с РЕАЛЬНЫМИ сервисами"""
        import os
        import tempfile

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from bot.handlers.ai_chat import handle_ai_message
        from bot.models import Base

        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        real_session = SessionLocal()

        # Симулируем ошибку внешнего AI API
        mock_ai_service = MagicMock()
        mock_ai_service.generate_response = AsyncMock(side_effect=Exception("AI API error"))
        mock_get_ai.return_value = mock_ai_service

        # Создаем реального пользователя
        from bot.services.user_service import UserService

        user_service = UserService(real_session)
        user = user_service.get_or_create_user(
            telegram_id=123456789, username="test_user", first_name="Тест"
        )
        user_service.update_user_profile(telegram_id=123456789, age=10, user_type="child")
        real_session.commit()

        def mock_get_db_real():
            return real_session

        try:
            with patch("bot.handlers.ai_chat.get_db", side_effect=lambda: mock_get_db_real()):
                await handle_ai_message(mock_message, mock_state)

            # Проверяем что пользователю отправлен ответ об ошибке
            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args
            if call_args:
                answer_text = ""
                if call_args[0]:
                    answer_text = call_args[0][0]
                elif call_args[1] and "text" in call_args[1]:
                    answer_text = call_args[1]["text"]
                assert (
                    "Ой" in answer_text
                    or "ошибка" in answer_text.lower()
                    or "попробуй" in answer_text.lower()
                )
        finally:
            real_session.close()
            engine.dispose()
            os.close(db_fd)
            os.unlink(db_path)

    def test_ai_chat_security_blocks_unsafe_content(self):
        """КРИТИЧНО: Тест что небезопасный контент блокируется реальной модерацией"""
        from bot.services.moderation_service import ContentModerationService

        moderation = ContentModerationService()

        # Тестируем реальную модерацию без моков
        unsafe_messages = [
            "наркотики",
            "купить оружие",
            "как убить",
        ]

        for message in unsafe_messages:
            is_safe, reason = moderation.is_safe_content(message)
            assert is_safe is False, f"ОПАСНО! Небезопасный контент не заблокирован: {message}"
            assert reason is not None, f"Должна быть причина блокировки для: {message}"

    def test_ai_chat_allows_safe_educational_content(self):
        """Тест что безопасный образовательный контент разрешен"""
        from bot.services.moderation_service import ContentModerationService

        moderation = ContentModerationService()

        safe_messages = [
            "помоги с математикой",
            "что такое фотосинтез",
            "объясни про дроби",
            "расскажи про планеты",
        ]

        for message in safe_messages:
            is_safe, reason = moderation.is_safe_content(message)
            assert is_safe is True, f"Безопасный контент заблокирован: {message}, причина: {reason}"

    def test_router_has_required_handlers(self):
        """Тест что роутер имеет необходимые обработчики"""
        from bot.handlers import ai_chat
        from bot.handlers.ai_chat import router

        assert router is not None
        assert hasattr(ai_chat, "start_ai_chat")
        assert hasattr(ai_chat, "handle_ai_message")

    def test_moderation_service_real_blocking(self):
        """КРИТИЧНО: Реальный тест модерации - проверяем что опасный контент блокируется"""
        from bot.services.moderation_service import ContentModerationService

        moderation = ContentModerationService()

        # Тестируем реальные опасные запросы
        dangerous_queries = [
            ("наркотики", "drugs"),
            ("купить оружие", "violence"),
            ("как убить", "violence"),
            ("порно", "adult_content"),
            ("секс", "adult_content"),
        ]

        for query, expected_category in dangerous_queries:
            is_safe, reason = moderation.is_safe_content(query)
            assert is_safe is False, f"КРИТИЧНО! Опасный контент не заблокирован: '{query}'"
            assert reason is not None, f"Должна быть причина блокировки для: '{query}'"
            # Проверяем что есть альтернативный безопасный ответ
            safe_response = moderation.get_safe_response_alternative("blocked_content")
            assert safe_response is not None
            assert len(safe_response) > 0
            # Проверяем что альтернативный ответ безопасен
            is_safe_response, _ = moderation.is_safe_content(safe_response)
            assert (
                is_safe_response is True
            ), f"Альтернативный ответ должен быть безопасным: {safe_response}"

    def test_moderation_service_sanitizes_ai_responses(self):
        """Тест что модерация очищает ответы AI от опасного контента"""
        from bot.services.moderation_service import ContentModerationService

        moderation = ContentModerationService()

        # Тестируем реальную очистку ответов
        potentially_unsafe_responses = [
            "Вот как можно купить наркотики...",
            "Это информация о сексе...",
        ]

        for response in potentially_unsafe_responses:
            sanitized = moderation.sanitize_ai_response(response)
            # Проверяем что очищенный ответ безопасен
            is_safe, _ = moderation.is_safe_content(sanitized)
            assert is_safe is True, f"Очищенный ответ должен быть безопасным: {sanitized}"
