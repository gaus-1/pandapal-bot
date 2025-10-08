"""
Тесты для AIResponseGenerator (SOLID)
Тестирование генерации ответов с DI
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from bot.services.ai_response_generator_solid import AIResponseGenerator, IModerator, IContextBuilder


class MockModerator(IModerator):
    """Мок модератора для тестов"""
    
    def __init__(self, is_safe=True, reason="Контент безопасен"):
        self.is_safe = is_safe
        self.reason = reason
    
    def moderate(self, text: str) -> tuple[bool, str]:
        return self.is_safe, self.reason


class MockContextBuilder(IContextBuilder):
    """Мок построителя контекста для тестов"""
    
    def __init__(self, context="Test context"):
        self.context = context
    
    def build(self, user_message: str, chat_history=None, user_age=None) -> str:
        return f"{self.context}: {user_message}"


class TestAIResponseGenerator:
    """Тесты для генератора ответов AI"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.moderator = MockModerator()
        self.context_builder = MockContextBuilder()
    
    @patch('bot.services.ai_response_generator_solid.genai')
    def test_init(self, mock_genai):
        """Тест инициализации"""
        mock_genai.configure = Mock()
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        generator = AIResponseGenerator(self.moderator, self.context_builder)
        
        assert generator.moderator == self.moderator
        assert generator.context_builder == self.context_builder
        assert generator.model == mock_model
        mock_genai.configure.assert_called_once()
        mock_genai.GenerativeModel.assert_called_once()
    
    @patch('bot.services.ai_response_generator_solid.genai')
    @pytest.mark.asyncio
    async def test_generate_response_safe_content(self, mock_genai):
        """Тест генерации ответа для безопасного контента"""
        # Настройка моков
        mock_genai.configure = Mock()
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Это безопасный ответ"
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model
        
        generator = AIResponseGenerator(self.moderator, self.context_builder)
        
        result = await generator.generate_response("Привет!")
        
        assert result == "Это безопасный ответ"
        mock_model.generate_content_async.assert_called_once()
    
    @patch('bot.services.ai_response_generator_solid.genai')
    @pytest.mark.asyncio
    async def test_generate_response_unsafe_content(self, mock_genai):
        """Тест генерации ответа для небезопасного контента"""
        # Настройка небезопасного модератора
        unsafe_moderator = MockModerator(is_safe=False, reason="Запрещенная тема: насилие")
        
        mock_genai.configure = Mock()
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        generator = AIResponseGenerator(unsafe_moderator, self.context_builder)
        
        result = await generator.generate_response("Как убить человека?")
        
        assert "Извините, но я не могу обсуждать эту тему" in result
        assert "Запрещенная тема: насилие" in result
        # Модель не должна вызываться для небезопасного контента
        mock_model.generate_content_async.assert_not_called()
    
    @patch('bot.services.ai_response_generator_solid.genai')
    @pytest.mark.asyncio
    async def test_generate_response_empty_response(self, mock_genai):
        """Тест генерации ответа когда модель возвращает пустой ответ"""
        mock_genai.configure = Mock()
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = None  # Пустой ответ
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model
        
        generator = AIResponseGenerator(self.moderator, self.context_builder)
        
        result = await generator.generate_response("Вопрос")
        
        assert "Извините, не смог сгенерировать ответ" in result
    
    @patch('bot.services.ai_response_generator_solid.genai')
    @pytest.mark.asyncio
    async def test_generate_response_exception(self, mock_genai):
        """Тест генерации ответа при исключении"""
        mock_genai.configure = Mock()
        mock_model = Mock()
        mock_model.generate_content_async = AsyncMock(side_effect=Exception("API Error"))
        mock_genai.GenerativeModel.return_value = mock_model
        
        generator = AIResponseGenerator(self.moderator, self.context_builder)
        
        result = await generator.generate_response("Вопрос")
        
        assert "Ой, что-то пошло не так" in result
    
    @patch('bot.services.ai_response_generator_solid.genai')
    def test_get_model_info(self, mock_genai):
        """Тест получения информации о модели"""
        mock_genai.configure = Mock()
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        generator = AIResponseGenerator(self.moderator, self.context_builder)
        
        info = generator.get_model_info()
        
        assert "model" in info
        assert "temperature" in info
        assert "max_tokens" in info
        assert "public_name" in info
        assert info["public_name"] == "PandaPalAI"
    
    @patch('bot.services.ai_response_generator_solid.genai')
    @pytest.mark.asyncio
    async def test_generate_response_with_history(self, mock_genai):
        """Тест генерации ответа с историей чата"""
        mock_genai.configure = Mock()
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Ответ с учетом истории"
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Настройка контекст-билдера с историей
        context_builder = MockContextBuilder("Context with history")
        context_builder.build = Mock(return_value="Context with history: Новый вопрос")
        
        generator = AIResponseGenerator(self.moderator, context_builder)
        
        history = [{"role": "user", "content": "Предыдущий вопрос"}]
        result = await generator.generate_response("Новый вопрос", history, user_age=10)
        
        assert result == "Ответ с учетом истории"
        # Проверяем что контекст-билдер был вызван с правильными параметрами
        context_builder.build.assert_called_once_with("Новый вопрос", history, 10)
    
    @patch('bot.services.ai_response_generator_solid.genai')
    @pytest.mark.asyncio
    async def test_dependency_injection(self, mock_genai):
        """Тест правильности внедрения зависимостей"""
        mock_genai.configure = Mock()
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        custom_moderator = MockModerator()
        custom_context_builder = MockContextBuilder()
        
        generator = AIResponseGenerator(custom_moderator, custom_context_builder)
        
        assert generator.moderator is custom_moderator
        assert generator.context_builder is custom_context_builder
