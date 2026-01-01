"""
Интеграционные тесты для SOLID AI архитектуры
Тестирование взаимодействия всех компонентов с Yandex Cloud
"""

import pytest

from bot.services.ai_context_builder import ContextBuilder
from bot.services.ai_moderator import ContentModerator
from bot.services.ai_service_solid import YandexAIService
from bot.services.yandex_ai_response_generator import YandexAIResponseGenerator


class TestAISolidIntegration:
    """Интеграционные тесты AI архитектуры"""

    @pytest.mark.asyncio
    async def test_full_ai_flow_safe_content(self):
        """Тест полного потока AI для безопасного контента"""
        # Создание реальных компонентов
        moderator = ContentModerator()
        context_builder = ContextBuilder()
        generator = YandexAIResponseGenerator(moderator, context_builder)
        service = YandexAIService()

        # Тест с реальным безопасным вопросом
        result = await service.generate_response("Что такое фотосинтез?", user_age=10)

        # Проверяем что получили ответ
        assert result is not None
        assert len(result) > 0
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_full_ai_flow_unsafe_content(self):
        """Тест полного потока AI для небезопасного контента"""
        # Создание реальных компонентов
        moderator = ContentModerator()
        context_builder = ContextBuilder()
        generator = YandexAIResponseGenerator(moderator, context_builder)
        service = YandexAIService()

        # Тест с реальным небезопасным вопросом
        result = await service.generate_response("как курить", user_age=12)

        # Проверяем что модерация сработала
        assert "Извините, но я не могу обсуждать эту тему" in result
        assert isinstance(result, str)

    def test_moderator_integration(self):
        """Тест интеграции модератора"""
        moderator = ContentModerator()

        # Тест различных типов контента
        test_cases = [
            ("Привет! Как дела?", True),
            ("Помоги с математикой", True),
            ("как курить", False),
            ("где купить наркотики", False),
            ("Что такое солнце?", True),
        ]

        for text, expected_safe in test_cases:
            is_safe, reason = moderator.moderate(text)
            assert is_safe == expected_safe
            if expected_safe:
                assert "безопасен" in reason.lower()
            else:
                assert "запрещен" in reason.lower()

    def test_context_builder_integration(self):
        """Тест интеграции построителя контекста"""
        context_builder = ContextBuilder()

        # Тест с историей и возрастом
        history = [
            {"role": "user", "content": "Привет"},
            {"role": "ai", "content": "Привет! Как дела?"},
            {"role": "user", "content": "Хорошо, спасибо"},
        ]

        context = context_builder.build("А что такое математика?", history, user_age=8)

        assert "ребенок 6-8 лет" in context
        assert "простыми словами" in context
        assert "Предыдущие сообщения:" in context
        assert "Пользователь: Привет" in context
        assert "AI: Привет! Как дела?" in context
        assert "Текущий вопрос: А что такое математика?" in context

    def test_solid_principles_compliance(self):
        """Тест соблюдения SOLID принципов"""
        # SRP - каждый класс имеет одну ответственность
        moderator = ContentModerator()
        context_builder = ContextBuilder()

        # Проверяем что модератор только модерирует
        assert hasattr(moderator, "moderate")
        assert not hasattr(moderator, "build")  # Не должен строить контекст

        # Проверяем что контекст-билдер только строит контекст
        assert hasattr(context_builder, "build")
        assert not hasattr(context_builder, "moderate")  # Не должен модерировать

        # DIP - зависимости от абстракций, а не от конкретных реализаций
        # YandexAIResponseGenerator принимает интерфейсы, а не конкретные классы
        generator = YandexAIResponseGenerator(moderator, context_builder)
        assert generator.moderator == moderator
        assert generator.context_builder == context_builder

    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Тест обработки ошибок в архитектуре"""
        # Создание реальных компонентов
        moderator = ContentModerator()
        context_builder = ContextBuilder()
        generator = YandexAIResponseGenerator(moderator, context_builder)
        service = YandexAIService()

        # Тест с реальным запросом - проверяем что система работает стабильно
        result = await service.generate_response("Тест")

        # Проверяем что получили ответ (не ошибку)
        assert result is not None
        assert isinstance(result, str)

    def test_performance_characteristics(self):
        """Тест характеристик производительности"""
        import time

        moderator = ContentModerator()
        context_builder = ContextBuilder()

        # Тест скорости модерации
        start_time = time.time()
        for i in range(100):
            moderator.moderate(f"Тестовое сообщение {i}")
        moderation_time = time.time() - start_time

        # Модерация должна быть быстрой (< 1 секунды для 100 сообщений)
        assert moderation_time < 1.0

        # Тест скорости построения контекста
        start_time = time.time()
        for i in range(100):
            context_builder.build(f"Вопрос {i}", user_age=10)
        context_time = time.time() - start_time

        # Построение контекста должно быть быстрым
        assert context_time < 1.0
