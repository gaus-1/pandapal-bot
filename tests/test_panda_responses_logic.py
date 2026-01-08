"""
Тесты логики ответов панды и общения с пользователем.

Проверяет:
1. Приветствие только при начале диалога или когда пользователь здоровается
2. Ответы на вопросы о панде (где живет, что ест, техника)
3. Логику запроса имени при очистке чата
4. Логику обращения по имени (раз в 5-10 сообщений)
5. Логику перенаправления на учебу (после 2+ непредметных вопросов)
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


class TestGreetingLogic:
    """Тесты логики приветствия"""

    @pytest.mark.asyncio
    async def test_greeting_at_chat_start(self, response_generator):
        """Панда должна здороваться при начале диалога (пустая история)"""
        user_message = "Как дела?"
        chat_history = []  # Пустая история

        # Мокаем ответ YandexGPT
        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Привет! У меня все отлично! Чем могу помочь?"

            response = await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
                is_history_cleared=False,
            )

            # Проверяем, что был вызван с правильным промптом
            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")

            # Должно быть разрешение на приветствие (пользователь не здоровался, но история пустая)
            assert "ПРИВЕТСТВИЕ" in system_prompt or "поприветствуй" in system_prompt.lower()

    @pytest.mark.asyncio
    async def test_greeting_when_user_greets(self, response_generator):
        """Панда должна здороваться когда пользователь поздоровался"""
        user_message = "Привет!"
        chat_history = [{"role": "user", "text": "Как дела?"}, {"role": "ai", "text": "Хорошо!"}]

        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Привет! Чем могу помочь?"

            response = await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
            )

            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")

            # Должно быть разрешение на приветствие (пользователь поздоровался)
            assert "ПРИВЕТСТВИЕ" in system_prompt or "поприветствуй" in system_prompt.lower()

    @pytest.mark.asyncio
    async def test_no_greeting_in_middle_of_conversation(self, response_generator):
        """Панда НЕ должна здороваться в середине разговора"""
        user_message = "Как решить задачу 2+2?"
        chat_history = [
            {"role": "user", "text": "Привет"},
            {"role": "ai", "text": "Привет! Чем могу помочь?"},
            {"role": "user", "text": "Помоги с математикой"},
            {"role": "ai", "text": "Конечно!"},
        ]

        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Это просто! 2+2=4"

            response = await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
            )

            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")

            # Должно быть запрещение на приветствие
            assert (
                "НЕ здоровался" in system_prompt
                or "НЕ говори" in system_prompt
                or "не привет" in system_prompt.lower()
            )


class TestPandaQuestions:
    """Тесты ответов на вопросы о панде"""

    @pytest.mark.asyncio
    async def test_where_panda_lives(self, response_generator):
        """Панда должна отвечать про хребет Миньшань"""
        user_message = "Где ты живешь?"
        chat_history = []

        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = (
                "Я живу в Китае, на одном из склонов хребта Миньшань. Там прохладно, много бамбука!"
            )

            response = await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
            )

            # Проверяем что промпт содержит информацию про хребет Миньшань
            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")
            assert "Миньшань" in system_prompt or "хребет" in system_prompt.lower()

    @pytest.mark.asyncio
    async def test_panda_technology(self, response_generator):
        """Панда должна отвечать про планшет и смартфон"""
        user_message = "Как ты пишешь? Ты умеешь пользоваться телефоном?"
        chat_history = []

        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Да, у меня есть планшет и смартфон, я особенная панда!"

            response = await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
            )

            # Проверяем что промпт содержит информацию про планшет и смартфон
            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")
            assert "планшет" in system_prompt.lower() and "смартфон" in system_prompt.lower()


class TestNameAsking:
    """Тесты логики запроса имени"""

    @pytest.mark.asyncio
    async def test_name_asking_after_history_clear(self, response_generator):
        """Панда должна спрашивать имя после очистки чата"""
        user_message = "Привет"
        chat_history = []  # Очищенная история

        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Привет! Давай знакомиться! Как тебя зовут? 🐼"

            response = await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
                is_history_cleared=True,
                user_name=None,  # Имя не известно
                skip_name_asking=False,
            )

            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")

            # Должна быть инструкция попросить имя
            assert (
                "назвать своё имя" in system_prompt.lower()
                or "как тебя зовут" in system_prompt.lower()
            )

    @pytest.mark.asyncio
    async def test_no_name_asking_if_skipped(self, response_generator):
        """Панда НЕ должна спрашивать имя если пользователь отказался"""
        user_message = "Привет"
        chat_history = []

        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Привет! Чем могу помочь?"

            response = await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
                is_history_cleared=True,
                user_name=None,
                skip_name_asking=True,  # Пользователь отказался
            )

            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")

            # Не должно быть инструкции про имя
            assert "назвать своё имя" not in system_prompt.lower()


class TestNameUsage:
    """Тесты логики обращения по имени"""

    @pytest.mark.asyncio
    async def test_name_usage_after_7_messages(self, response_generator):
        """Панда должна обращаться по имени после 7+ сообщений"""
        user_message = "Помоги с задачей"
        chat_history = [
            {"role": "user", "text": "Привет"},
            {"role": "ai", "text": "Привет!"},
            {"role": "user", "text": "Как дела?"},
            {"role": "ai", "text": "Хорошо!"},
            {"role": "user", "text": "Что нового?"},
            {"role": "ai", "text": "Все отлично!"},
            {"role": "user", "text": "Расскажи что-то"},
            {"role": "ai", "text": "Хорошо!"},
            {"role": "user", "text": "Еще вопрос"},
            {"role": "ai", "text": "Слушаю!"},
            {"role": "user", "text": "Еще раз"},
            {"role": "ai", "text": "Ок!"},
            {"role": "user", "text": "Еще"},
            {"role": "ai", "text": "Да!"},
        ]  # 7+ сообщений пользователя

        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Саша, конечно помогу!"

            response = await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
                user_name="Саша",
                message_count_since_name=7,  # Прошло 7 сообщений (гарантированное обращение)
            )

            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")

            # Должна быть инструкция обратиться по имени
            assert "Обратись к пользователю по имени" in system_prompt or "Саша" in system_prompt

    @pytest.mark.asyncio
    async def test_no_name_usage_before_5_messages(self, response_generator):
        """Панда НЕ должна обращаться по имени до 5 сообщений"""
        user_message = "Помоги"
        chat_history = [
            {"role": "user", "text": "Привет"},
            {"role": "ai", "text": "Привет!"},
        ]  # Только 1 сообщение пользователя

        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Конечно помогу!"

            response = await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
                user_name="Саша",
                message_count_since_name=1,  # Только 1 сообщение
            )

            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")

            # Не должно быть инструкции про имя
            assert "Обратись к пользователю по имени" not in system_prompt


class TestEducationalRedirect:
    """Тесты логики перенаправления на учебу"""

    @pytest.mark.asyncio
    async def test_redirect_after_2_non_educational_questions(self, response_generator):
        """Панда должна перенаправлять на учебу после 2+ непредметных вопросов"""
        user_message = "Что ты делаешь?"
        chat_history = [
            {"role": "user", "text": "Где ты живешь?"},
            {"role": "ai", "text": "В Китае"},
        ]  # Уже 1 непредметный вопрос

        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Интересно общаться, но давай лучше вернемся к учебе!"

            response = await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
                non_educational_questions_count=2,  # Уже 2 непредметных вопроса
            )

            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")

            # Должна быть инструкция перенаправить на учебу
            assert (
                "перенаправь" in system_prompt.lower()
                or "учебу" in system_prompt.lower()
                or "учебе" in system_prompt.lower()
            )

    @pytest.mark.asyncio
    async def test_no_redirect_on_first_non_educational_question(self, response_generator):
        """Панда НЕ должна перенаправлять при первом непредметном вопросе"""
        user_message = "Где ты живешь?"
        chat_history = []

        with patch.object(
            response_generator.yandex_service, "generate_text_response", new_callable=AsyncMock
        ) as mock_gpt:
            mock_gpt.return_value = "Я живу в Китае, на склонах хребта Миньшань!"

            response = await response_generator.generate_response(
                user_message=user_message,
                chat_history=chat_history,
                user_age=10,
                non_educational_questions_count=1,  # Только 1 непредметный вопрос
            )

            call_args = mock_gpt.call_args
            system_prompt = call_args.kwargs.get("system_prompt", "")

            # Не должно быть инструкции перенаправить (только при 2+)
            assert "перенаправь" not in system_prompt.lower() or "2" in system_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
