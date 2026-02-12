"""
Unit тесты для API endpoints
"""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp.test_utils import make_mocked_request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.api.metrics_endpoint import MetricsEndpoint
from bot.api.miniapp import (
    miniapp_ai_chat,
    miniapp_auth,
    miniapp_get_achievements,
    miniapp_get_chat_history,
    miniapp_get_dashboard,
    miniapp_get_progress,
    miniapp_get_subjects,
    miniapp_get_user,
    miniapp_update_user,
)
from bot.api.premium_endpoints import create_yookassa_payment, handle_successful_payment
from bot.models import Base


class TestMiniAppEndpoints:
    """Тесты для Mini App endpoints"""

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

    @pytest.mark.asyncio
    async def test_miniapp_auth_invalid_initdata(self, real_db_session):
        """Тест аутентификации с невалидными данными"""

        class MockRequest:
            async def json(self):
                return {"initData": "invalid_data"}

        request = MockRequest()

        with patch("bot.api.miniapp.auth.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            with patch("bot.api.miniapp.auth.TelegramWebAppAuth") as mock_auth:
                mock_auth_instance = MagicMock()
                mock_auth_instance.validate_init_data.return_value = None
                mock_auth.return_value = mock_auth_instance

                response = await miniapp_auth(request)
                assert response.status == 403

    @pytest.mark.asyncio
    async def test_miniapp_get_user_not_found(self, real_db_session):
        """Тест получения несуществующего пользователя"""
        request = make_mocked_request(
            "GET",
            "/api/miniapp/user/999999",
            match_info={"telegram_id": "999999"},
        )

        with patch("bot.api.miniapp.auth.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            with patch("bot.api.miniapp.auth.verify_resource_owner") as mock_verify:
                mock_verify.return_value = (True, None)
                response = await miniapp_get_user(request)
            assert response.status == 404

    @pytest.mark.asyncio
    async def test_miniapp_get_progress(self, real_db_session):
        """Тест получения прогресса пользователя"""
        from bot.models import User
        from bot.services.user_service import UserService

        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(
            telegram_id=123456, username="test", first_name="Test"
        )
        real_db_session.commit()

        request = make_mocked_request(
            "GET",
            "/api/miniapp/progress/123456",
            match_info={"telegram_id": "123456"},
        )

        with patch("bot.api.miniapp.progress.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            with patch("bot.api.miniapp.progress.require_owner", return_value=None):
                response = await miniapp_get_progress(request)
            assert response.status == 200

            # web.json_response возвращает Response, читаем body напрямую
            import json

            body = response._body if hasattr(response, "_body") else b"{}"
            data = json.loads(body.decode("utf-8"))
            assert data["success"] is True
            assert "progress" in data or "stats" in data

    @pytest.mark.asyncio
    async def test_miniapp_get_achievements(self, real_db_session):
        """Тест получения достижений"""
        from bot.models import User
        from bot.services.user_service import UserService

        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(
            telegram_id=123456, username="test", first_name="Test"
        )
        real_db_session.commit()

        request = make_mocked_request(
            "GET",
            "/api/miniapp/achievements/123456",
            match_info={"telegram_id": "123456"},
        )

        with patch("bot.api.miniapp.progress.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            with patch("bot.api.miniapp.progress.require_owner", return_value=None):
                response = await miniapp_get_achievements(request)
            assert response.status == 200

            # web.json_response возвращает Response, читаем body напрямую
            import json

            body = response._body if hasattr(response, "_body") else b"{}"
            data = json.loads(body.decode("utf-8"))
            assert data["success"] is True
            assert "achievements" in data or "stats" in data

    @pytest.mark.asyncio
    async def test_miniapp_get_dashboard(self, real_db_session):
        """Тест получения дашборда"""
        from bot.models import User
        from bot.services.user_service import UserService

        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(
            telegram_id=123456, username="test", first_name="Test"
        )
        real_db_session.commit()

        request = make_mocked_request(
            "GET",
            "/api/miniapp/dashboard/123456",
            match_info={"telegram_id": "123456"},
        )

        with patch("bot.api.miniapp.progress.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            with patch("bot.api.miniapp.progress.require_owner", return_value=None):
                response = await miniapp_get_dashboard(request)
            assert response.status == 200

            import json

            body = response._body if hasattr(response, "_body") else b"{}"
            data = json.loads(body.decode("utf-8"))
            assert data["success"] is True
            assert "stats" in data or "progress" in data

    @pytest.mark.asyncio
    async def test_miniapp_get_chat_history(self, real_db_session):
        """Тест получения истории чата"""
        from bot.models import User
        from bot.services.user_service import UserService

        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(
            telegram_id=123456, username="test", first_name="Test"
        )
        real_db_session.commit()

        request = make_mocked_request(
            "GET",
            "/api/miniapp/chat/history/123456",
            match_info={"telegram_id": "123456"},
        )

        with patch("bot.api.miniapp.other.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            with patch("bot.api.miniapp.other.require_owner", return_value=None):
                response = await miniapp_get_chat_history(request)
            assert response.status == 200

            import json

            body = response._body if hasattr(response, "_body") else b"{}"
            data = json.loads(body.decode("utf-8"))
            assert data["success"] is True
            assert "history" in data or "messages" in data

    @pytest.mark.asyncio
    async def test_miniapp_get_subjects(self):
        """Тест получения списка предметов"""
        request = make_mocked_request("GET", "/api/miniapp/subjects")

        response = await miniapp_get_subjects(request)
        assert response.status == 200

        import json

        body = response._body if hasattr(response, "_body") else b"{}"
        data = json.loads(body.decode("utf-8"))
        assert data["success"] is True
        assert "subjects" in data
        assert isinstance(data["subjects"], list)

    @pytest.mark.asyncio
    async def test_miniapp_update_user(self, real_db_session):
        """Тест обновления пользователя"""
        from bot.models import User
        from bot.services.user_service import UserService

        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(
            telegram_id=123456, username="test", first_name="Test"
        )
        real_db_session.commit()

        class MockRequest:
            async def json(self):
                return {"age": 12, "grade": 6}

            @property
            def match_info(self):
                return {"telegram_id": "123456"}

        request = MockRequest()

        with patch("bot.api.miniapp.auth.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            with patch("bot.api.miniapp.auth.verify_resource_owner") as mock_verify:
                mock_verify.return_value = (True, None)
                response = await miniapp_update_user(request)
            assert response.status == 200

            import json

            body = response._body if hasattr(response, "_body") else b"{}"
            data = json.loads(body.decode("utf-8"))
            assert data["success"] is True


class TestPremiumEndpoints:
    """Тесты для Premium endpoints"""

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

    @pytest.mark.asyncio
    async def test_create_premium_invoice_invalid_plan(self, real_db_session):
        """Тест создания invoice с невалидным планом"""

        class MockRequest:
            async def json(self):
                return {"telegram_id": 123456, "plan_id": "invalid"}

        request = MockRequest()

        with patch("bot.api.premium_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            response = await create_yookassa_payment(request)
            assert response.status == 400

    @pytest.mark.asyncio
    async def test_create_premium_invoice_user_not_found(self, real_db_session):
        """Тест создания invoice для несуществующего пользователя"""

        class MockRequest:
            async def json(self):
                return {"telegram_id": 999999, "plan_id": "month"}

        request = MockRequest()

        with patch("bot.api.premium_endpoints.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            response = await create_yookassa_payment(request)
            assert response.status == 404


class TestMetricsEndpoint:
    """Тесты для Metrics endpoint"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Тест health check endpoint"""
        endpoint = MetricsEndpoint()
        request = MagicMock()

        with patch("bot.database.engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            mock_engine.connect.return_value.__exit__.return_value = None

            with patch("bot.services.ai_service_solid.get_ai_service") as mock_ai:
                mock_ai.return_value = MagicMock()
                response = await endpoint.health_check(request)
            assert response.status == 200

            import json

            body = response._body if hasattr(response, "_body") else b"{}"
            data = json.loads(body.decode("utf-8"))
            assert "status" in data
            assert "components" in data
            assert "database" in data["components"]

    @pytest.mark.asyncio
    async def test_health_check_database_error(self):
        """Тест health check при ошибке БД"""
        endpoint = MetricsEndpoint()
        request = MagicMock()

        with patch("bot.database.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("Database connection failed")

            with patch("bot.services.ai_service_solid.get_ai_service") as mock_ai:
                mock_ai.return_value = MagicMock()
                response = await endpoint.health_check(request)
            assert response.status == 503

            import json

            body = response._body if hasattr(response, "_body") else b"{}"
            data = json.loads(body.decode("utf-8"))
            assert data["components"]["database"] == "unhealthy"
