"""
Расширенные тесты SQL инъекций для URL параметров
Проверка защиты endpoints от SQL инъекций через URL параметры
"""

import os
import tempfile

import pytest
from aiohttp.test_utils import make_mocked_request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.api.miniapp import miniapp_get_user
from bot.models import Base, User
from bot.services.user_service import UserService


class TestSQLInjectionURLParams:
    """Тесты SQL инъекций через URL параметры"""

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
    async def test_sql_injection_in_telegram_id_union(self, real_db_session, test_user):
        """Тест: UNION-based SQL инъекция в telegram_id параметре"""
        from unittest.mock import patch

        malicious_id = "123456789' UNION SELECT username, password FROM users--"

        request = make_mocked_request(
            "GET",
            f"/api/miniapp/user/{malicious_id}",
            match_info={"telegram_id": malicious_id},
        )

        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            response = await miniapp_get_user(request)

            # Должна вернуться ошибка валидации, а не данные
            assert response.status in [400, 404], "Должна вернуться ошибка валидации"

    @pytest.mark.asyncio
    async def test_sql_injection_in_telegram_id_boolean(self, real_db_session, test_user):
        """Тест: Boolean-based SQL инъекция в telegram_id"""
        from unittest.mock import patch

        malicious_id = "123456789' OR '1'='1"

        request = make_mocked_request(
            "GET",
            f"/api/miniapp/user/{malicious_id}",
            match_info={"telegram_id": malicious_id},
        )

        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            response = await miniapp_get_user(request)

            # Должна вернуться ошибка валидации
            assert response.status in [400, 404]

    @pytest.mark.asyncio
    async def test_sql_injection_in_telegram_id_comment(self, real_db_session, test_user):
        """Тест: SQL инъекция с комментариями в telegram_id"""
        from unittest.mock import patch

        malicious_id = "123456789'--"

        request = make_mocked_request(
            "GET",
            f"/api/miniapp/user/{malicious_id}",
            match_info={"telegram_id": malicious_id},
        )

        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            response = await miniapp_get_user(request)

            # Должна вернуться ошибка валидации
            assert response.status in [400, 404]

    @pytest.mark.asyncio
    async def test_sql_injection_special_chars(self, real_db_session, test_user):
        """Тест: Специальные символы SQL в telegram_id"""
        from unittest.mock import patch

        malicious_inputs = [
            "'; DROP TABLE users; --",
            '" OR 1=1 --',
            "admin'--",
            "1' OR '1'='1",
            "1' UNION SELECT * FROM users--",
        ]

        for malicious_id in malicious_inputs:
            request = make_mocked_request(
                "GET",
                f"/api/miniapp/user/{malicious_id}",
                match_info={"telegram_id": malicious_id},
            )

            with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = real_db_session
                mock_get_db.return_value.__exit__.return_value = None

                response = await miniapp_get_user(request)

                # Должна вернуться ошибка валидации или 404, но НЕ 500
                assert response.status != 500, f"Не должна возвращаться 500 для {malicious_id}"
                assert response.status in [
                    400,
                    404,
                ], f"Должна быть ошибка валидации для {malicious_id}"

                # Проверяем что таблица users всё ещё существует
                from sqlalchemy import text

                result = real_db_session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                )
                assert (
                    result.fetchone() is not None
                ), f"Таблица users должна существовать после {malicious_id}"
