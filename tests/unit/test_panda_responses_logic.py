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

    @pytest.mark.asyncio
    async def test_history_message_limit_slice(self, response_generator):
        """При 25 сообщениях и history_message_limit=20 в API уходит список длины 20."""
        history_25 = [
            {"role": "user" if i % 2 == 0 else "assistant", "text": f"msg {i}"}
            for i in range(25)
        ]
        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Ответ."
            await response_generator.generate_response(
                user_message="Вопрос",
                chat_history=history_25,
                user_age=10,
                history_message_limit=20,
            )
            call_args = mock_gpt.call_args
            chat_history_passed = call_args.kwargs.get("chat_history", [])
            assert len(chat_history_passed) == 20, (
                "В Yandex API должна уходить история, обрезанная до 20 сообщений"
            )


class TestShouldAskClarification:
    """Уточняющий вопрос при коротком неоднозначном продолжении."""

    def test_short_continuation_with_long_reply_returns_true(self, response_generator):
        """«а ещё?» + длинный ответ в истории → True."""
        long_reply = "Фотосинтез — это процесс. " * 20  # > 180 символов
        history = [
            {"role": "user", "text": "Что такое фотосинтез?"},
            {"role": "assistant", "text": long_reply},
        ]
        assert response_generator._should_ask_clarification("а ещё?", history) is True

    def test_full_question_returns_false(self, response_generator):
        """«Расскажи про фотосинтез» → False (длинное или не из списка)."""
        history = [{"role": "assistant", "text": "Да, конечно. " * 30}]
        assert (
            response_generator._should_ask_clarification("Расскажи про фотосинтез", history)
            is False
        )

    def test_empty_history_returns_false(self, response_generator):
        """Пустая история → False."""
        assert response_generator._should_ask_clarification("а ещё?", []) is False
        assert response_generator._should_ask_clarification("а ещё?", None) is False

    def test_short_last_reply_returns_false(self, response_generator):
        """Последний ответ assistant короче 180 символов → False."""
        history = [
            {"role": "user", "text": "Привет"},
            {"role": "assistant", "text": "Привет!"},
        ]
        assert response_generator._should_ask_clarification("а ещё?", history) is False

    @pytest.mark.asyncio
    async def test_generate_response_returns_clarification_without_api_call(
        self, response_generator
    ):
        """При «а ещё?» и длинном ответе в истории возвращается фиксированная фраза, API не вызывается."""
        from bot.services.yandex_ai_response_generator import _CLARIFICATION_RESPONSE

        long_reply = "Фотосинтез — это процесс превращения света в энергию. " * 10
        history = [
            {"role": "user", "text": "Что такое фотосинтез?"},
            {"role": "assistant", "text": long_reply},
        ]
        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            result = await response_generator.generate_response(
                user_message="а ещё?",
                chat_history=history,
                user_age=10,
            )
            assert result == _CLARIFICATION_RESPONSE
            mock_gpt.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
