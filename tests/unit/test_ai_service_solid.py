"""
Тесты для GeminiAIService (SOLID)
Тестирование фасада AI сервиса
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from bot.services.ai_service_solid import GeminiAIService, get_ai_service


class TestGeminiAIService:
    """Тесты для AI сервиса"""
    
    @patch('bot.services.ai_service_solid.AIResponseGenerator')
    @patch('bot.services.ai_service_solid.ContentModerator')
    @patch('bot.services.ai_service_solid.ContextBuilder')
    def test_init(self, mock_context_builder, mock_moderator, mock_generator):
        """Тест инициализации сервиса"""
        mock_generator_instance = Mock()
        mock_generator.return_value = mock_generator_instance
        
        service = GeminiAIService()
        
        # Проверяем что зависимости были созданы
        mock_moderator.assert_called_once()
        mock_context_builder.assert_called_once()
        mock_generator.assert_called_once()
        
        # Проверяем что генератор был инжектирован
        assert service.response_generator == mock_generator_instance
    
    @patch('bot.services.ai_service_solid.AIResponseGenerator')
    @patch('bot.services.ai_service_solid.ContentModerator')
    @patch('bot.services.ai_service_solid.ContextBuilder')
    @pytest.mark.asyncio
    async def test_generate_response(self, mock_context_builder, mock_moderator, mock_generator):
        """Тест генерации ответа"""
        mock_generator_instance = Mock()
        mock_generator_instance.generate_response = AsyncMock(return_value="Тестовый ответ")
        mock_generator.return_value = mock_generator_instance
        
        service = GeminiAIService()
        
        result = await service.generate_response("Привет!", [{"role": "user", "content": "Тест"}], 10)
        
        assert result == "Тестовый ответ"
        mock_generator_instance.generate_response.assert_called_once_with("Привет!", [{"role": "user", "content": "Тест"}], 10)
    
    @patch('bot.services.ai_service_solid.AIResponseGenerator')
    @patch('bot.services.ai_service_solid.ContentModerator')
    @patch('bot.services.ai_service_solid.ContextBuilder')
    def test_get_model_info(self, mock_context_builder, mock_moderator, mock_generator):
        """Тест получения информации о модели"""
        mock_generator_instance = Mock()
        mock_generator_instance.get_model_info.return_value = {
            "model": "gemini-pro",
            "temperature": "0.7",
            "max_tokens": "2048",
            "public_name": "PandaPalAI"
        }
        mock_generator.return_value = mock_generator_instance
        
        service = GeminiAIService()
        
        info = service.get_model_info()
        
        assert info["model"] == "gemini-pro"
        assert info["temperature"] == "0.7"
        assert info["max_tokens"] == "2048"
        assert info["public_name"] == "PandaPalAI"
        mock_generator_instance.get_model_info.assert_called_once()
    
    @patch('bot.services.ai_service_solid.GeminiAIService')
    def test_get_ai_service_singleton(self, mock_service_class):
        """Тест singleton паттерна"""
        mock_instance = Mock()
        mock_service_class.return_value = mock_instance
        
        # Первый вызов
        service1 = get_ai_service()
        
        # Второй вызов
        service2 = get_ai_service()
        
        # Должны быть одинаковые экземпляры
        assert service1 is service2
        assert service1 is mock_instance
        
        # Класс должен быть вызван только один раз
        mock_service_class.assert_called_once()
    
    @patch('bot.services.ai_service_solid.AIResponseGenerator')
    @patch('bot.services.ai_service_solid.ContentModerator')
    @patch('bot.services.ai_service_solid.ContextBuilder')
    @pytest.mark.asyncio
    async def test_facade_pattern(self, mock_context_builder, mock_moderator, mock_generator):
        """Тест фасад паттерна - делегирование всех вызовов"""
        mock_generator_instance = Mock()
        mock_generator_instance.generate_response = AsyncMock(return_value="Ответ через фасад")
        mock_generator_instance.get_model_info.return_value = {"model": "test"}
        mock_generator.return_value = mock_generator_instance
        
        service = GeminiAIService()
        
        # Тест делегирования generate_response
        result = await service.generate_response("Тест")
        assert result == "Ответ через фасад"
        mock_generator_instance.generate_response.assert_called_once_with("Тест", None, None)
        
        # Тест делегирования get_model_info
        info = service.get_model_info()
        assert info == {"model": "test"}
        mock_generator_instance.get_model_info.assert_called_once()
    
    @patch('bot.services.ai_service_solid.AIResponseGenerator')
    @patch('bot.services.ai_service_solid.ContentModerator')
    @patch('bot.services.ai_service_solid.ContextBuilder')
    def test_dependency_injection_verification(self, mock_context_builder, mock_moderator, mock_generator):
        """Тест правильности внедрения зависимостей"""
        mock_moderator_instance = Mock()
        mock_context_builder_instance = Mock()
        mock_generator_instance = Mock()
        
        mock_moderator.return_value = mock_moderator_instance
        mock_context_builder.return_value = mock_context_builder_instance
        mock_generator.return_value = mock_generator_instance
        
        service = GeminiAIService()
        
        # Проверяем что генератор получил правильные зависимости
        mock_generator.assert_called_once_with(mock_moderator_instance, mock_context_builder_instance)
    
    @patch('bot.services.ai_service_solid.AIResponseGenerator')
    @patch('bot.services.ai_service_solid.ContentModerator')
    @patch('bot.services.ai_service_solid.ContextBuilder')
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_context_builder, mock_moderator, mock_generator):
        """Тест обработки ошибок в фасаде"""
        mock_generator_instance = Mock()
        mock_generator_instance.generate_response = AsyncMock(side_effect=Exception("Test error"))
        mock_generator.return_value = mock_generator_instance
        
        service = GeminiAIService()
        
        # Ошибка должна пробрасываться через фасад
        with pytest.raises(Exception, match="Test error"):
            await service.generate_response("Тест")
