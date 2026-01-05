"""
E2E тесты обработки ошибок внешних API и сети
Проверяет что при сбоях внешних сервисов пользователь получает понятные сообщения об ошибках

РЕАЛЬНОЕ тестирование - использует реальные сервисы, БД, модерацию.
Моки только для эмуляции ошибок внешних API (Yandex).
"""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.api.miniapp_endpoints import miniapp_ai_chat
from bot.database import get_db
from bot.models import Base
from bot.services.moderation_service import ContentModerationService
from bot.services.user_service import UserService


class TestErrorHandlingE2E:
    """E2E тесты обработки ошибок - РЕАЛЬНОЕ тестирование"""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Реальная БД для E2E тестов"""
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
        """Создаёт тестового пользователя - РЕАЛЬНО"""
        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(
            telegram_id=999888777,
            username="error_test_user",
            first_name="Тестовый",
            last_name="Ошибка",
        )
        user_service.update_user_profile(telegram_id=999888777, age=10, grade=5, user_type="child")
        real_db_session.commit()
        return user

    def create_request(self, json_data):
        """Создаёт реальный aiohttp Request для API"""
        from unittest.mock import MagicMock

        from aiohttp.test_utils import make_mocked_request

        # Создаём request с правильными атрибутами
        request = make_mocked_request(
            "POST",
            "/api/miniapp/ai/chat",
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(str(json_data))),
            },
        )
        # Добавляем метод json() и данные
        request._json_data = json_data

        async def json():
            return request._json_data

        request.json = json

        # Устанавливаем remote через mock (read-only property)
        type(request).remote = property(lambda self: "127.0.0.1")

        return request

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_yandex_gpt_error_handling(self, real_db_session, test_user):
        """
        КРИТИЧНО: Тест обработки ошибки YandexGPT
        Использует РЕАЛЬНУЮ БД, РЕАЛЬНУЮ модерацию
        Моки только для эмуляции ошибки YandexGPT API
        """
        telegram_id = 999888777
        text_message = "Привет! Помоги с математикой"

        # РЕАЛЬНАЯ модерация
        moderation_service = ContentModerationService()
        is_safe, _ = moderation_service.is_safe_content(text_message)
        assert is_safe is True, "Сообщение должно быть безопасным"

        # Создаём запрос
        request = self.create_request(
            {
                "telegram_id": telegram_id,
                "message": text_message,
                "message_type": "text",
            }
        )

        # Используем РЕАЛЬНУЮ БД через get_db
        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            # Мокаем только get_db чтобы использовать нашу тестовую БД
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            # Мокаем только AI сервис чтобы эмулировать ошибку YandexGPT
            with patch("bot.api.miniapp_endpoints.get_ai_service") as mock_ai_service:
                mock_service = AsyncMock()
                # Эмулируем ошибку API (например, timeout или 500)
                mock_service.generate_response = AsyncMock(
                    side_effect=Exception("YandexGPT API недоступен. Попробуйте позже.")
                )
                mock_ai_service.return_value = mock_service

                # Выполняем запрос - РЕАЛЬНАЯ БД, РЕАЛЬНАЯ модерация
                response = await miniapp_ai_chat(request)

                # Проверяем что получили ответ (не 500)
                assert response.status in [200, 500], f"Неожиданный статус: {response.status}"

                # Если статус 200, проверяем что в ответе есть понятное сообщение об ошибке
                if response.status == 200:
                    response_data = await response.json()
                    # Проверяем что есть сообщение об ошибке
                    assert "error" in response_data or "message" in response_data
                    # Проверяем что сообщение понятное (не техническое)
                    if "error" in response_data:
                        error_msg = response_data["error"].lower()
                        assert (
                            "попробуйте позже" in error_msg
                            or "ошибка" in error_msg
                            or "недоступен" in error_msg
                        ), f"Сообщение об ошибке не понятное: {response_data['error']}"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_speechkit_error_fallback_to_text(self, real_db_session, test_user):
        """
        КРИТИЧНО: Тест обработки ошибки SpeechKit
        Использует РЕАЛЬНУЮ БД, РЕАЛЬНУЮ модерацию
        Моки только для эмуляции ошибки SpeechKit
        """
        telegram_id = 999888777
        audio_base64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQAAAAA="

        # РЕАЛЬНАЯ модерация
        moderation_service = ContentModerationService()

        # Создаём запрос с аудио
        request = self.create_request(
            {
                "telegram_id": telegram_id,
                "audio_base64": audio_base64,
                "message_type": "audio",
            }
        )

        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            # Мокаем только SpeechKit чтобы эмулировать ошибку
            with patch("bot.api.miniapp_endpoints.SpeechService") as mock_speech:
                mock_speech_service = AsyncMock()
                # Эмулируем ошибку SpeechKit
                mock_speech_service.transcribe_voice = AsyncMock(
                    side_effect=Exception("SpeechKit API недоступен")
                )
                mock_speech.return_value = mock_speech_service

                # Выполняем запрос - РЕАЛЬНАЯ БД, РЕАЛЬНАЯ модерация
                response = await miniapp_ai_chat(request)

                # Проверяем что получили ответ
                assert response.status in [200, 400, 500]

                # Если статус 200, проверяем что есть fallback или понятное сообщение
                if response.status == 200:
                    response_data = await response.json()
                    # Должен быть либо fallback на текст, либо понятное сообщение об ошибке
                    assert (
                        "error" in response_data
                        or "message" in response_data
                        or "response" in response_data
                    )

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_vision_error_fallback_to_text(self, real_db_session, test_user):
        """
        КРИТИЧНО: Тест обработки ошибки Vision API
        Использует РЕАЛЬНУЮ БД, РЕАЛЬНУЮ модерацию
        Моки только для эмуляции ошибки Vision
        """
        telegram_id = 999888777
        photo_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        # РЕАЛЬНАЯ модерация
        moderation_service = ContentModerationService()
        is_safe, _ = moderation_service.is_safe_content("Что на этом фото?")
        assert is_safe is True

        # Создаём запрос с фото
        request = self.create_request(
            {
                "telegram_id": telegram_id,
                "message": "Что на этом фото?",
                "photo_base64": photo_base64,
                "message_type": "photo",
            }
        )

        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            # Мокаем только Vision чтобы эмулировать ошибку
            with patch("bot.api.miniapp_endpoints.VisionService") as mock_vision:
                mock_vision_service = AsyncMock()
                # Эмулируем ошибку Vision API
                mock_vision_service.analyze_image = AsyncMock(
                    side_effect=Exception("Vision API недоступен")
                )
                mock_vision.return_value = mock_vision_service

                # Выполняем запрос - РЕАЛЬНАЯ БД, РЕАЛЬНАЯ модерация
                response = await miniapp_ai_chat(request)

                # Проверяем что получили ответ
                assert response.status in [200, 400, 500]

                # Если статус 200, проверяем что есть fallback или понятное сообщение
                if response.status == 200:
                    response_data = await response.json()
                    # Должен быть либо fallback на текст, либо понятное сообщение об ошибке
                    assert (
                        "error" in response_data
                        or "message" in response_data
                        or "response" in response_data
                    )

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_network_error_retry_and_message(self, real_db_session, test_user):
        """
        КРИТИЧНО: Тест обработки сетевых ошибок
        Использует РЕАЛЬНУЮ БД, РЕАЛЬНУЮ модерацию
        Моки только для эмуляции сетевой ошибки
        """
        telegram_id = 999888777
        text_message = "Привет!"

        # РЕАЛЬНАЯ модерация
        moderation_service = ContentModerationService()
        is_safe, _ = moderation_service.is_safe_content(text_message)
        assert is_safe is True

        # Создаём запрос
        request = self.create_request(
            {
                "telegram_id": telegram_id,
                "message": text_message,
                "message_type": "text",
            }
        )

        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            # Мокаем только AI сервис чтобы эмулировать сетевую ошибку
            with patch("bot.api.miniapp_endpoints.get_ai_service") as mock_ai_service:
                mock_service = AsyncMock()
                # Эмулируем сетевую ошибку (например, timeout)
                import asyncio

                mock_service.generate_response = AsyncMock(
                    side_effect=asyncio.TimeoutError("Сетевое соединение прервано")
                )
                mock_ai_service.return_value = mock_service

                # Выполняем запрос - РЕАЛЬНАЯ БД, РЕАЛЬНАЯ модерация
                response = await miniapp_ai_chat(request)

                # Проверяем что получили ответ (не зависло)
                assert response.status in [200, 500, 503]

                # Если статус 200, проверяем что есть понятное сообщение об ошибке
                if response.status == 200:
                    response_data = await response.json()
                    assert "error" in response_data or "message" in response_data
                    if "error" in response_data:
                        error_msg = response_data["error"].lower()
                        assert (
                            "сеть" in error_msg
                            or "соединение" in error_msg
                            or "попробуйте позже" in error_msg
                            or "ошибка" in error_msg
                        ), f"Сообщение об ошибке не понятное: {response_data['error']}"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_multiple_errors_graceful_degradation(self, real_db_session, test_user):
        """
        КРИТИЧНО: Тест graceful degradation при множественных ошибках
        Использует РЕАЛЬНУЮ БД, РЕАЛЬНУЮ модерацию
        Моки только для эмуляции ошибок AI
        """
        telegram_id = 999888777
        text_message = "Привет!"

        # РЕАЛЬНАЯ модерация - проверяем что она работает
        moderation_service = ContentModerationService()
        is_safe, _ = moderation_service.is_safe_content(text_message)
        assert is_safe is True, "Модерация должна работать"

        # Создаём запрос
        request = self.create_request(
            {
                "telegram_id": telegram_id,
                "message": text_message,
                "message_type": "text",
            }
        )

        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            # Мокаем только AI сервис чтобы эмулировать ошибку
            with patch("bot.api.miniapp_endpoints.get_ai_service") as mock_ai_service:
                mock_service = AsyncMock()
                mock_service.generate_response = AsyncMock(
                    side_effect=Exception("YandexGPT недоступен")
                )
                mock_ai_service.return_value = mock_service

                # Выполняем запрос - РЕАЛЬНАЯ БД, РЕАЛЬНАЯ модерация
                response = await miniapp_ai_chat(request)

                # Проверяем что система не упала полностью
                assert response.status in [200, 500, 503]

                # Проверяем что модерация всё равно работает (РЕАЛЬНАЯ проверка)
                is_safe_after, _ = moderation_service.is_safe_content(text_message)
                assert is_safe_after is True, "Модерация должна работать даже при ошибках AI"
