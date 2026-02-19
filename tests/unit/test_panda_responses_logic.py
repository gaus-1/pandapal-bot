"""
Тесты логики ответов панды и промпта.

Проверяет, что системный промпт содержит:
- Роль PandaPal и правила структуры (абзацы, выделение, без повторов, списки).
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot.services.yandex_ai_response_generator import (
    IContextBuilder,
    IModerator,
    YandexAIResponseGenerator,
)


@pytest.fixture
def mock_moderator():
    """Мок модератора"""
    moderator = Mock(spec=IModerator)
    moderator.moderate = Mock(return_value=(True, None))
    return moderator


@pytest.fixture
def mock_context_builder():
    """Мок билдера контекста"""
    builder = Mock(spec=IContextBuilder)
    return builder


@pytest.fixture
def mock_knowledge_service():
    """Мок сервиса знаний"""
    from bot.services.knowledge_service import KnowledgeService

    service = Mock(spec=KnowledgeService)
    service.get_helpful_content = AsyncMock(return_value=[])
    service.format_knowledge_for_ai = Mock(return_value="")
    service.format_and_compress_knowledge_for_ai = Mock(return_value="")
    return service


@pytest.fixture
def response_generator(mock_moderator, mock_context_builder, mock_knowledge_service):
    """Создает генератор ответов с моками"""
    generator = YandexAIResponseGenerator(mock_moderator, mock_context_builder)
    generator.knowledge_service = mock_knowledge_service
    return generator


class TestPromptStructure:
    """Промпт содержит роль и правила структуры ответов."""

    @pytest.mark.asyncio
    async def test_prompt_contains_role_and_structure(self, response_generator):
        """Системный промпт содержит PandaPal и правила структуры (абзацы, выделение, без повторов)."""
        user_message = "Что такое 2+2?"
        chat_history = []

        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "2+2=4. Это сложение."

            await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
            )

            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")

            assert "PandaPal" in system_prompt or "pandapal" in system_prompt.lower()
            has_structure = (
                "абзац" in system_prompt.lower()
                or "структурируй" in system_prompt.lower()
                or "жирным" in system_prompt.lower()
                or "дублируй" in system_prompt.lower()
                or "список" in system_prompt.lower()
                or "выделяй" in system_prompt.lower()
            )
            assert has_structure, "Промпт должен содержать правила структуры ответов"

    @pytest.mark.asyncio
    async def test_prompt_no_repetitions_rule(self, response_generator):
        """Промпт содержит правило не повторять один и тот же блок."""
        user_message = "Помоги с задачей"
        chat_history = []

        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Конечно!"

            await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
            )

            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")

            assert "повтор" in system_prompt.lower() or "дублируй" in system_prompt.lower()

    @pytest.mark.asyncio
    async def test_prompt_visual_and_paragraphs(self, response_generator):
        """Промпт содержит визуал и разделение на абзацы."""
        user_message = "Нарисуй график"
        chat_history = []

        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Вот график."

            await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
            )

            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")

            assert (
                "визуал" in system_prompt.lower()
                or "график" in system_prompt.lower()
                or "абзац" in system_prompt.lower()
            )

    @pytest.mark.asyncio
    async def test_prompt_contains_motivation_and_structure_unchanged(self, response_generator):
        """Промпт содержит блок мотивации/иронии и правила структуры не отменяются."""
        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Давай разберёмся."
            await response_generator.generate_response(
                user_message="Не хочу решать",
                chat_history=[],
                user_age=10,
            )
            system_prompt = mock_gpt.call_args.kwargs.get("system_prompt", "")
        has_motivation = any(
            kw in system_prompt.lower()
            for kw in ["мотивац", "ирония", "подбадривай", "репетитор", "тон", "подбод"]
        )
        assert has_motivation, "Промпт должен содержать мотивацию/тон"
        has_structure = any(
            kw in system_prompt.lower() for kw in ["структур", "абзац", "список", "выделяй"]
        )
        assert has_structure
        assert "грамматик" in system_prompt.lower() or "правил" in system_prompt.lower()

    def test_prompt_builder_adds_gender_hint(self):
        """При передаче user_gender в промпте появляется подсказка о поле пользователя."""
        from bot.services.prompt_builder import PromptBuilder

        builder = PromptBuilder()
        prompt = builder.build_system_prompt(
            user_message="Привет",
            chat_history=[],
            user_gender="male",
        )
        assert "мужской" in prompt or "Пол пользователя" in prompt
        prompt_f = builder.build_system_prompt(
            user_message="Привет",
            chat_history=[],
            user_gender="female",
        )
        assert "женский" in prompt_f or "Пол пользователя" in prompt_f


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
