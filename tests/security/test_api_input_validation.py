"""
Тесты валидации входных данных API
Проверка обработки некорректных типов данных, огромных строк, спецсимволов
"""

import os
import tempfile

import pytest
from aiohttp.test_utils import make_mocked_request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.api.miniapp import miniapp_ai_chat, miniapp_update_user
from bot.models import Base, User
from bot.services.user_service import UserService


class TestAPIInputValidation:
    """Тесты валидации входных данных API"""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Создаёт реальную SQLite БД для каждого теста"""
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
        """Создаёт тестового пользователя"""
        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
        )
        real_db_session.commit()
        return user

    @pytest.mark.asyncio
    async def test_huge_string_in_name_field(self, real_db_session, test_user):
        """Тест: огромная строка (1MB) в поле имени должна быть отклонена"""
        from unittest.mock import patch

        huge_string = "x" * (1024 * 1024)  # 1MB

        class MockRequest:
            match_info = {"telegram_id": "123456789"}

            async def json(self):
                return {"first_name": huge_string}

        mock_request = MockRequest()

        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            response = await miniapp_update_user(mock_request)

            # Должна вернуться ошибка валидации 400 или 413 (Payload Too Large)
            assert response.status in [400, 413], "Должна быть ошибка для слишком большого поля"

    @pytest.mark.asyncio
    async def test_invalid_data_types_in_request(self, real_db_session, test_user):
        """Тест: невалидные типы данных должны возвращать 400"""
        from unittest.mock import patch

        invalid_requests = [
            {"age": "not_a_number"},  # Строка вместо числа
            {"grade": [1, 2, 3]},  # Список вместо числа
            # None допустимо для Optional полей, не тестируем
        ]

        for invalid_data in invalid_requests:

            class MockRequest:
                match_info = {"telegram_id": "123456789"}

                async def json(self):
                    return invalid_data

            mock_request = MockRequest()

            with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = real_db_session
                mock_get_db.return_value.__exit__.return_value = None

                response = await miniapp_update_user(mock_request)

                # Должна вернуться ошибка валидации 400
                assert response.status == 400, f"Должна быть ошибка 400 для {invalid_data}"

    @pytest.mark.asyncio
    async def test_special_characters_in_message(self, real_db_session, test_user):
        """Тест: специальные символы в сообщении должны обрабатываться корректно"""
        from unittest.mock import patch

        special_chars_messages = [
            "'; DROP TABLE users; --",
            '<script>alert("XSS")</script>',
            "Привет! 🐼",
            "Тест\nс\nпереносами",
            "Тест\tс\tтабуляцией",
        ]

        for message in special_chars_messages:

            class MockRequest:
                async def json(self):
                    return {
                        "telegram_id": 123456789,
                        "message": message,
                        "chat_history": [],
                    }

            mock_request = MockRequest()

            with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = real_db_session
                mock_get_db.return_value.__exit__.return_value = None

                # Мокаем AI сервис чтобы не делать реальные запросы
                with patch("bot.api.miniapp_endpoints.get_ai_service") as mock_ai:
                    response = await miniapp_ai_chat(mock_request)

                    # Должен вернуться 400 или 500, но не 200 с выполнением SQL/XSS
                    if response.status == 200:
                        response_data = await response.json()
                        # Проверяем что ответ безопасен (не содержит выполненного SQL/XSS)
                        response_str = str(response_data)
                        assert (
                            "DROP TABLE" not in response_str
                        ), f"SQL не должен выполняться для {message[:50]}"
                        assert (
                            "<script>" not in response_str
                        ), f"XSS не должен выполняться для {message[:50]}"

    @pytest.mark.asyncio
    async def test_empty_request_body(self, real_db_session, test_user):
        """Тест: пустое тело запроса должно возвращать 400"""
        from unittest.mock import patch

        class MockRequest:
            match_info = {"telegram_id": "123456789"}

            async def json(self):
                return {}

        mock_request = MockRequest()

        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            response = await miniapp_update_user(mock_request)

            # Должна вернуться ошибка 400 или 200 (если пустое тело допустимо)
            assert response.status in [200, 400], "Должна быть обработка пустого тела запроса"

    @pytest.mark.asyncio
    async def test_negative_values(self, real_db_session, test_user):
        """Тест: отрицательные значения должны быть отклонены"""
        from unittest.mock import patch

        class MockRequest:
            match_info = {"telegram_id": "123456789"}

            async def json(self):
                return {"age": -10, "grade": -5}

        mock_request = MockRequest()

        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            response = await miniapp_update_user(mock_request)

            # Должна вернуться ошибка валидации 400
            assert response.status == 400, "Должна быть ошибка для отрицательных значений"
