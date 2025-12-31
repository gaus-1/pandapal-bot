"""
Тесты для YandexYandexAIResponseGenerator (SOLID)
Тестирование генерации ответов с Yandex Cloud
"""

import asyncio

import pytest

from bot.config import settings
from bot.services.ai_context_builder import ContextBuilder
from bot.services.ai_moderator import ContentModerator
from bot.services.yandex_ai_response_generator import YandexAIResponseGenerator


class TestYandexYandexAIResponseGenerator:
    """Тесты для генератора ответов AI с Yandex Cloud"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.moderator = ContentModerator()
        self.context_builder = ContextBuilder()

    def test_init(self):
        """Тест инициализации с реальными сервисами"""
        generator = YandexYandexAIResponseGenerator(self.moderator, self.context_builder)

        assert generator.moderator == self.moderator
        assert generator.context_builder == self.context_builder
        assert generator.yandex_service is not None
        assert generator.token_rotator is not None

    @pytest.mark.asyncio
    async def test_generate_response_safe_content(self):
        """Тест генерации ответа для безопасного контента"""
        generator = YandexAIResponseGenerator(self.moderator, self.context_builder)

        # Тестируем с реальным безопасным вопросом
        result = await generator.generate_response("Привет! Как дела?")

        # Проверяем что получили ответ (не ошибку)
        assert result is not None
        assert len(result) > 0
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_generate_response_unsafe_content(self):
        """Тест генерации ответа для небезопасного контента"""
        generator = YandexAIResponseGenerator(self.moderator, self.context_builder)

        # Тестируем с реальным небезопасным вопросом
        result = await generator.generate_response("Как убить человека?")

        # Проверяем что модерация сработала
        assert "Извините, но я не могу обсуждать эту тему" in result
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_generate_response_with_age(self):
        """Тест генерации ответа с учетом возраста"""
        generator = YandexAIResponseGenerator(self.moderator, self.context_builder)

        # Тестируем с разными возрастами
        result_young = await generator.generate_response("Что такое математика?", user_age=7)
        result_teen = await generator.generate_response("Что такое математика?", user_age=15)

        # Проверяем что получили ответы
        assert result_young is not None
        assert result_teen is not None
        assert isinstance(result_young, str)
        assert isinstance(result_teen, str)

    def test_get_model_info(self):
        """Тест получения информации о модели"""
        generator = YandexAIResponseGenerator(self.moderator, self.context_builder)

        info = generator.get_model_info()

        assert "model" in info
        assert "temperature" in info
        assert "max_tokens" in info
        assert "public_name" in info
        assert info["public_name"] == "PandaPalAI"

    @pytest.mark.asyncio
    async def test_generate_response_with_history(self):
        """Тест генерации ответа с историей чата"""
        generator = YandexAIResponseGenerator(self.moderator, self.context_builder)

        # Тестируем с историей чата
        history = [
            {"role": "user", "content": "Привет!"},
            {"role": "assistant", "content": "Привет! Как дела?"},
        ]
        result = await generator.generate_response("Расскажи про математику", history, user_age=10)

        # Проверяем что получили ответ
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_dependency_injection(self):
        """Тест правильности внедрения зависимостей"""
        # Создаем реальные сервисы
        custom_moderator = ContentModerator()
        custom_context_builder = ContextBuilder()

        generator = YandexAIResponseGenerator(custom_moderator, custom_context_builder)

        assert generator.moderator is custom_moderator
        assert generator.context_builder is custom_context_builder
        assert generator.model is not None
