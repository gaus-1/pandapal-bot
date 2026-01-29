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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
