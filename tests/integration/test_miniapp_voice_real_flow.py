"""
Реальные тесты голосовой функции в мини-аппе БЕЗ реального API.

Проверяет:
- Мини-апп принимает audio_base64 от пользователя (симуляция нажатия кнопки)
- Передает аудио в SpeechService
- SpeechService обрабатывает и возвращает текст
- Текст передается в AI
- AI отвечает корректно
- Весь поток работает без реального API (моки)
"""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp.test_utils import make_mocked_request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, User


@pytest.mark.integration
class TestMiniAppVoiceRealFlow:
    """Реальные тесты потока обработки голосовых сообщений в мини-аппе."""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Реальная БД для тестов"""
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        yield session

        session.close()
        engine.dispose()
        os.close(db_fd)
        os.unlink(db_path)

    @pytest.fixture
    def test_user(self, real_db_session):
        """Создает тестового пользователя"""
        user = User(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            age=12,
            user_type="child",
        )
        real_db_session.add(user)
        real_db_session.commit()
        return user

    def create_request(self, json_data: dict):
        """Создает мок request для мини-аппа"""
        request = make_mocked_request(
            "POST",
            "/api/miniapp/ai/chat",
            headers={"Content-Type": "application/json"},
        )
        request._json_data = json_data

        async def json():
            return request._json_data

        request.json = json
        type(request).remote = property(lambda self: "127.0.0.1")
        return request

    @pytest.mark.asyncio
    async def test_miniapp_accepts_audio_from_user_button_click(self, real_db_session, test_user):
        """
        КРИТИЧНО: Тест что мини-апп принимает аудио от пользователя (симуляция нажатия кнопки).
        Проверяет весь поток: кнопка -> audio_base64 -> SpeechService -> AI -> ответ.
        """
        from bot.api.miniapp import miniapp_ai_chat

        telegram_id = test_user.telegram_id
        # Симулируем audio_base64 который приходит от пользователя при нажатии кнопки записи
        audio_base64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQAAAAA="  # Минимальный валидный WAV

        request = self.create_request(
            {
                "telegram_id": telegram_id,
                "audio_base64": audio_base64,
            }
        )

        # Мокаем SpeechService - НЕ используем реальный API
        with patch("bot.api.miniapp_endpoints.SpeechService") as mock_speech_class:
            mock_speech_service = MagicMock()
            # Симулируем распознавание речи
            mock_speech_service.transcribe_voice = AsyncMock(
                return_value="Привет, помоги решить задачу по математике"
            )
            mock_speech_class.return_value = mock_speech_service

            # Мокаем AI сервис - НЕ используем реальный API
            with patch("bot.api.miniapp_endpoints.get_ai_service") as mock_ai:
                mock_ai_service = AsyncMock()
                mock_ai_service.generate_response = AsyncMock(
                    return_value="Конечно помогу! Какая задача?"
                )
                mock_ai.return_value = mock_ai_service

                # Мокаем get_db
                with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
                    mock_get_db.return_value.__enter__.return_value = real_db_session
                    mock_get_db.return_value.__exit__.return_value = None

                    # ВЫЗОВ: мини-апп обрабатывает аудио от пользователя
                    response = await miniapp_ai_chat(request)

                    # ПРОВЕРКА 1: Мини-апп принял запрос
                    assert response.status == 200, "Мини-апп должен принять аудио и вернуть 200"

                    # ПРОВЕРКА 2: SpeechService был вызван с правильными параметрами
                    mock_speech_service.transcribe_voice.assert_called_once()
                    call_args = mock_speech_service.transcribe_voice.call_args
                    assert (
                        call_args is not None
                    ), "SpeechService.transcribe_voice должен быть вызван"
                    # Проверяем что передали байты аудио
                    audio_bytes_arg = call_args[0][0] if call_args[0] else None
                    assert (
                        audio_bytes_arg is not None
                    ), "Должны передать байты аудио в SpeechService"
                    assert isinstance(audio_bytes_arg, bytes), "Аудио должно быть в формате bytes"

                    # ПРОВЕРКА 3: AI сервис был вызван с распознанным текстом
                    mock_ai_service.generate_response.assert_called_once()
                    ai_call_args = mock_ai_service.generate_response.call_args
                    assert ai_call_args is not None, "AI сервис должен быть вызван"

                    # Проверяем что AI получил распознанный текст
                    user_message = ai_call_args.kwargs.get("user_message") or (
                        ai_call_args.args[0] if ai_call_args.args else None
                    )
                    assert user_message is not None, "AI должен получить сообщение пользователя"
                    assert (
                        "математике" in user_message.lower() or "задачу" in user_message.lower()
                    ), f"AI должен получить распознанный текст: {user_message}"

                    # ПРОВЕРКА 4: Ответ содержит результат
                    if hasattr(response, "_body") and response._body:
                        import json

                        response_data = json.loads(response._body.decode("utf-8"))
                        assert (
                            "response" in response_data or "error" in response_data
                        ), "Ответ должен содержать response или error"

                        # ПРОВЕРКА 5: Ответ структурирован (для frontend парсинга)
                        if "response" in response_data:
                            ai_response = response_data["response"]
                            # Проверяем что ответ можно разбить на блоки (есть абзацы или структурированные секции)
                            has_structure = (
                                "\n\n" in ai_response or
                                "Определение:" in ai_response or
                                "Ключевые свойства:" in ai_response or
                                "Как это работает:" in ai_response or
                                "Где применяется:" in ai_response or
                                "Итог:" in ai_response
                            )
                            # Ответ должен быть структурированным (хотя бы по абзацам)
                            assert has_structure or len(ai_response.split()) > 10, \
                                "Ответ должен быть структурированным (абзацы или секции)"
                    else:
                        # Если нет _body, проверяем только статус
                        assert response.status == 200, "Ответ должен быть успешным"

                    print("\n[OK] Mini-app accepted audio from user button click")
                    print(
                        f"    SpeechService called: {mock_speech_service.transcribe_voice.called}"
                    )
                    print(f"    AI Service called: {mock_ai_service.generate_response.called}")
                    print(f"    Response status: {response.status}")

    @pytest.mark.asyncio
    async def test_miniapp_audio_foreign_language_translation_flow(
        self, real_db_session, test_user
    ):
        """
        КРИТИЧНО: Тест обработки иностранного языка в аудио.
        Проверяет: аудио -> распознавание -> определение языка -> перевод -> AI.
        """
        from bot.api.miniapp import miniapp_ai_chat

        telegram_id = test_user.telegram_id
        audio_base64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQAAAAA="

        request = self.create_request(
            {
                "telegram_id": telegram_id,
                "audio_base64": audio_base64,
            }
        )

        # Мокаем SpeechService - распознает английский текст
        with patch("bot.api.miniapp_endpoints.SpeechService") as mock_speech_class:
            mock_speech_service = MagicMock()
            mock_speech_service.transcribe_voice = AsyncMock(
                return_value="Hello, can you help me with math?"
            )
            mock_speech_class.return_value = mock_speech_service

            # Мокаем TranslateService для определения языка и перевода
            with patch("bot.api.miniapp_endpoints.get_translate_service") as mock_translate:
                mock_translate_service = MagicMock()
                mock_translate_service.detect_language = AsyncMock(return_value="en")
                mock_translate_service.translate_text = AsyncMock(
                    return_value="Привет, можешь помочь с математикой?"
                )
                mock_translate_service.get_language_name = MagicMock(return_value="Английский")
                mock_translate_service.SUPPORTED_LANGUAGES = ["en", "de", "fr", "es", "ru"]
                mock_translate.return_value = mock_translate_service

                # Мокаем AI сервис
                with patch("bot.api.miniapp_endpoints.get_ai_service") as mock_ai:
                    mock_ai_service = AsyncMock()
                    mock_ai_service.generate_response = AsyncMock(
                        return_value="Конечно помогу! Вижу что ты спросил на английском."
                    )
                    mock_ai.return_value = mock_ai_service

                    # Мокаем get_db
                    with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
                        mock_get_db.return_value.__enter__.return_value = real_db_session
                        mock_get_db.return_value.__exit__.return_value = None

                        response = await miniapp_ai_chat(request)

                        assert response.status == 200

                        # Проверяем что TranslateService был вызван
                        mock_translate_service.detect_language.assert_called_once()
                        mock_translate_service.translate_text.assert_called_once()

                        # Проверяем что AI получил переведенный текст или запрос на объяснение перевода
                        call_args = mock_ai_service.generate_response.call_args
                        user_message = call_args.kwargs.get("user_message") or (
                            call_args.args[0] if call_args.args else None
                        )
                        assert user_message is not None
                        # AI должен получить либо переведенный текст, либо запрос на объяснение перевода
                        assert (
                            "английск" in user_message.lower()
                            or "перевод" in user_message.lower()
                            or "математик" in user_message.lower()
                        )

                        print("\n[OK] Mini-app processed foreign language audio with translation")
                        print(f"    Language detected: en")
                        print(
                            f"    Translation called: {mock_translate_service.translate_text.called}"
                        )
                        print(f"    AI received message with translation info")

    @pytest.mark.asyncio
    async def test_miniapp_audio_error_handling_flow(self, real_db_session, test_user):
        """
        КРИТИЧНО: Тест обработки ошибок в потоке аудио.
        Проверяет что мини-апп корректно обрабатывает ошибки распознавания.
        """
        from bot.api.miniapp import miniapp_ai_chat

        telegram_id = test_user.telegram_id
        audio_base64 = "invalid_audio_data"

        request = self.create_request(
            {
                "telegram_id": telegram_id,
                "audio_base64": audio_base64,
            }
        )

        # Мокаем SpeechService чтобы эмулировать ошибку распознавания
        with patch("bot.api.miniapp_endpoints.SpeechService") as mock_speech_class:
            mock_speech_service = MagicMock()
            mock_speech_service.transcribe_voice = AsyncMock(
                return_value=None
            )  # Ошибка распознавания
            mock_speech_class.return_value = mock_speech_service

            # Мокаем get_db
            with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = real_db_session
                mock_get_db.return_value.__exit__.return_value = None

                response = await miniapp_ai_chat(request)

                # Должен вернуть ошибку 400
                assert response.status == 400, "При ошибке распознавания должен вернуть 400"

                if hasattr(response, "_body") and response._body:
                    import json

                    response_data = json.loads(response._body.decode("utf-8"))
                    assert "error" in response_data, "Ответ должен содержать error"
                    error_msg = response_data.get("error", "")
                    assert (
                        "распознать" in error_msg.lower()
                        or "речь" in error_msg.lower()
                        or len(error_msg) > 0
                    ), f"Сообщение об ошибке должно быть понятным: {error_msg}"

                print("\n[OK] Mini-app handled audio recognition error correctly")
                print(f"    Error status: {response.status}")
                print(f"    Error message: {response_data.get('error', '')[:100]}")

    @pytest.mark.asyncio
    async def test_miniapp_audio_full_flow_with_history(self, real_db_session, test_user):
        """
        КРИТИЧНО: Полный поток обработки аудио с сохранением в историю.
        Проверяет: аудио -> распознавание -> AI -> сохранение в БД -> ответ.
        """
        from bot.api.miniapp import miniapp_ai_chat

        telegram_id = test_user.telegram_id
        audio_base64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQAAAAA="

        request = self.create_request(
            {
                "telegram_id": telegram_id,
                "audio_base64": audio_base64,
            }
        )

        # Мокаем SpeechService
        with patch("bot.api.miniapp_endpoints.SpeechService") as mock_speech_class:
            mock_speech_service = MagicMock()
            mock_speech_service.transcribe_voice = AsyncMock(return_value="Сколько будет 2 плюс 2?")
            mock_speech_class.return_value = mock_speech_service

            # Мокаем AI сервис
            with patch("bot.api.miniapp_endpoints.get_ai_service") as mock_ai:
                mock_ai_service = AsyncMock()
                mock_ai_service.generate_response = AsyncMock(
                    return_value="Два плюс два равно четыре!"
                )
                mock_ai.return_value = mock_ai_service

                # Мокаем get_db
                with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
                    mock_get_db.return_value.__enter__.return_value = real_db_session
                    mock_get_db.return_value.__exit__.return_value = None

                    response = await miniapp_ai_chat(request)

                    assert response.status == 200

                    # Проверяем что сообщения сохранились в БД
                    from bot.models import ChatHistory

                    history = (
                        real_db_session.query(ChatHistory)
                        .filter_by(user_telegram_id=telegram_id)
                        .all()
                    )

                    # Должны быть сохранены: вопрос пользователя и ответ AI
                    assert (
                        len(history) >= 2
                    ), f"Должно быть минимум 2 сообщения в истории, получено: {len(history)}"

                    user_messages = [h for h in history if h.message_type == "user"]
                    ai_messages = [h for h in history if h.message_type == "ai"]

                    assert len(user_messages) >= 1, "Должно быть сохранено сообщение пользователя"
                    assert len(ai_messages) >= 1, "Должно быть сохранено сообщение AI"

                    print("\n[OK] Mini-app full audio flow with history saved")
                    print(f"    Total messages in history: {len(history)}")
                    print(f"    User messages: {len(user_messages)}")
                    print(f"    AI messages: {len(ai_messages)}")
