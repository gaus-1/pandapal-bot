"""
Тесты для YandexAIService (SOLID)
Тестирование фасада AI сервиса
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot.services.ai_service_solid import YandexAIService, get_ai_service


class TestYandexAIService:
    """Тесты для AI сервиса"""

    @patch("bot.services.ai_service_solid.YandexAIResponseGenerator")
    @patch("bot.services.ai_service_solid.ContentModerator")
    @patch("bot.services.ai_service_solid.ContextBuilder")
    def test_init(self, mock_context_builder, mock_moderator, mock_generator):
        """Тест инициализации сервиса"""
        mock_generator_instance = Mock()
        mock_generator.return_value = mock_generator_instance

        service = YandexAIService()

        # Проверяем что зависимости были созданы
        mock_moderator.assert_called_once()
        mock_context_builder.assert_called_once()
        mock_generator.assert_called_once()

        # Проверяем что генератор был инжектирован
        assert service.response_generator == mock_generator_instance

    @patch("bot.services.ai_service_solid.YandexAIResponseGenerator")
    @patch("bot.services.ai_service_solid.ContentModerator")
    @patch("bot.services.ai_service_solid.ContextBuilder")
    @pytest.mark.asyncio
    async def test_generate_response(self, mock_context_builder, mock_moderator, mock_generator):
        """Тест генерации ответа"""
        mock_generator_instance = Mock()
        mock_generator_instance.generate_response = AsyncMock(return_value="Тестовый ответ")
        mock_generator.return_value = mock_generator_instance

        service = YandexAIService()

        result = await service.generate_response(
            "Привет!", [{"role": "user", "content": "Тест"}], 10
        )

        assert result == "Тестовый ответ"
        # Проверяем что метод вызван с правильными обязательными параметрами
        # Остальные параметры имеют значения по умолчанию
        mock_generator_instance.generate_response.assert_called_once()
        call_args = mock_generator_instance.generate_response.call_args
        assert call_args[0][0] == "Привет!"
        assert call_args[0][1] == [{"role": "user", "content": "Тест"}]
        assert call_args[0][2] == 10

    @patch("bot.services.ai_service_solid.YandexAIResponseGenerator")
    @patch("bot.services.ai_service_solid.ContentModerator")
    @patch("bot.services.ai_service_solid.ContextBuilder")
    def test_get_model_info(self, mock_context_builder, mock_moderator, mock_generator):
        """Тест получения информации о модели Yandex"""
        mock_generator_instance = Mock()
        mock_generator_instance.get_model_info.return_value = {
            "model": "yandexgpt-lite",
            "temperature": "0.7",
            "max_tokens": "2000",
            "public_name": "PandaPal",
        }
        mock_generator.return_value = mock_generator_instance

        service = YandexAIService()

        info = service.get_model_info()

        assert info["model"] == "yandexgpt-lite"
        assert info["temperature"] == "0.7"
        mock_generator_instance.get_model_info.assert_called_once()

    def test_get_ai_service_singleton(self):
        """Singleton: один экземпляр на процесс, класс создаётся один раз."""
        import bot.services.ai_service_solid as ai_module

        mock_instance = Mock()
        mock_class = Mock(return_value=mock_instance)
        original_cache = ai_module._ai_service
        ai_module._ai_service = None
        try:
            with patch.object(ai_module, "YandexAIService", mock_class):
                service1 = get_ai_service()
                service2 = get_ai_service()
                assert service1 is service2, "Должен возвращаться один и тот же экземпляр"
                assert service1 is mock_instance, "Экземпляр — подставленный мок"
                assert mock_class.call_count == 1, "Класс должен быть вызван один раз"
        finally:
            ai_module._ai_service = original_cache

    @patch("bot.services.ai_service_solid.YandexAIResponseGenerator")
    @patch("bot.services.ai_service_solid.ContentModerator")
    @patch("bot.services.ai_service_solid.ContextBuilder")
    @pytest.mark.asyncio
    async def test_facade_pattern(self, mock_context_builder, mock_moderator, mock_generator):
        """Тест фасад паттерна - делегирование всех вызовов"""
        mock_generator_instance = Mock()
        mock_generator_instance.generate_response = AsyncMock(return_value="Ответ через фасад")
        mock_generator_instance.get_model_info.return_value = {"model": "yandexgpt-lite"}
        mock_generator.return_value = mock_generator_instance

        service = YandexAIService()

        # Тест делегирования generate_response
        result = await service.generate_response("Тест")
        assert result == "Ответ через фасад"
        mock_generator_instance.generate_response.assert_called_once_with(
            "Тест", None, None, None, None, False, 0, False, 0, False, False, None, None
        )

        # Тест делегирования get_model_info
        info = service.get_model_info()
        assert info == {"model": "yandexgpt-lite"}
        mock_generator_instance.get_model_info.assert_called_once()

    @patch("bot.services.ai_service_solid.YandexAIResponseGenerator")
    @patch("bot.services.ai_service_solid.ContentModerator")
    @patch("bot.services.ai_service_solid.ContextBuilder")
    def test_dependency_injection_verification(
        self, mock_context_builder, mock_moderator, mock_generator
    ):
        """Тест правильности внедрения зависимостей"""
        mock_moderator_instance = Mock()
        mock_context_builder_instance = Mock()
        mock_generator_instance = Mock()

        mock_moderator.return_value = mock_moderator_instance
        mock_context_builder.return_value = mock_context_builder_instance
        mock_generator.return_value = mock_generator_instance

        service = YandexAIService()

        # Проверяем что генератор получил правильные зависимости
        mock_generator.assert_called_once_with(
            mock_moderator_instance, mock_context_builder_instance
        )

    @patch("bot.services.ai_service_solid.YandexAIResponseGenerator")
    @patch("bot.services.ai_service_solid.ContentModerator")
    @patch("bot.services.ai_service_solid.ContextBuilder")
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_context_builder, mock_moderator, mock_generator):
        """Тест обработки ошибок в фасаде"""
        mock_generator_instance = Mock()
        mock_generator_instance.generate_response = AsyncMock(side_effect=Exception("Test error"))
        mock_generator.return_value = mock_generator_instance

        service = YandexAIService()

        # Ошибка должна пробрасываться через фасад
        with pytest.raises(Exception, match="Test error"):
            await service.generate_response("Тест")
