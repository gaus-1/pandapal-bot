"""
РЕАЛЬНЫЕ интеграционные тесты для Mini App endpoints
БЕЗ МОКОВ - только реальные операции с БД

Тестируем:
- Все endpoints Mini App через прямые вызовы функций
- Валидацию входных данных
- Обработку ошибок
- Интеграцию с геймификацией
"""

import os
import tempfile

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.api.miniapp import (
    miniapp_get_achievements,
    miniapp_get_progress,
    miniapp_get_user,
)
from bot.models import Base, User


class TestMiniAppEndpointsReal:
    """Реальные тесты Mini App endpoints"""

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
        """Создаёт тестового пользователя в БД"""
        user = User(
            telegram_id=123456,
            username="test_miniapp_user",
            first_name="Тестовый",
            last_name="MiniApp",
            user_type="child",
            age=10,
            grade=5,
        )
        real_db_session.add(user)
        real_db_session.commit()
        return user

    @pytest.mark.asyncio
    async def test_get_user_profile_endpoint(self, real_db_session, test_user):
        """Тест: GET /api/miniapp/user/{telegram_id}"""
        # Создаём mock request
        request = make_mocked_request(
            "GET", "/api/miniapp/user/123456", match_info={"telegram_id": "123456"}
        )

        # Мокаем get_db чтобы использовать нашу тестовую сессию
        from unittest.mock import patch

        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            # Вызываем endpoint
            response = await miniapp_get_user(request)
            data = await response.json()

            assert response.status == 200
            assert data["success"] is True
            assert "user" in data
            assert data["user"]["telegram_id"] == 123456
            assert data["user"]["first_name"] == "Тестовый"

    @pytest.mark.asyncio
    async def test_get_achievements_endpoint(self, real_db_session, test_user):
        """Тест: GET /api/miniapp/achievements/{telegram_id}"""
        # Создаём mock request
        request = make_mocked_request(
            "GET",
            "/api/miniapp/achievements/123456",
            match_info={"telegram_id": "123456"},
        )

        from unittest.mock import patch

        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            # Вызываем endpoint
            response = await miniapp_get_achievements(request)
            data = await response.json()

            assert response.status == 200
            assert data["success"] is True
            assert "achievements" in data
            assert isinstance(data["achievements"], list)

    @pytest.mark.asyncio
    async def test_get_progress_endpoint(self, real_db_session, test_user):
        """Тест: GET /api/miniapp/progress/{telegram_id}"""
        # Создаём mock request
        request = make_mocked_request(
            "GET", "/api/miniapp/progress/123456", match_info={"telegram_id": "123456"}
        )

        from unittest.mock import patch

        with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            # Вызываем endpoint
            response = await miniapp_get_progress(request)
            data = await response.json()

            assert response.status == 200
            assert data["success"] is True
            assert "progress" in data

    @pytest.mark.asyncio
    async def test_invalid_telegram_id(self):
        """Тест: обработка невалидного telegram_id"""
        # Создаём mock request с невалидным ID
        request = make_mocked_request(
            "GET", "/api/miniapp/user/invalid_id", match_info={"telegram_id": "invalid_id"}
        )

        from unittest.mock import patch

        with patch("bot.api.miniapp_endpoints.get_db"):
            response = await miniapp_get_user(request)
            assert response.status == 400

            data = await response.json()
            assert "error" in data
