"""
Unit тесты для health check endpoints
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp.test_utils import make_mocked_request

from bot.api.metrics_endpoint import MetricsEndpoint


class TestHealthCheck:
    """Тесты для health check endpoints"""

    @pytest.mark.asyncio
    async def test_health_check_web_server(self):
        """Тест health check в web_server.py"""
        from web_server import PandaPalBotServer

        server = PandaPalBotServer()
        server.bot = MagicMock()
        server.bot.get_me = AsyncMock(return_value=MagicMock(username="test_bot"))
        server.bot.get_webhook_info = AsyncMock(
            return_value=MagicMock(url="https://test.com/webhook")
        )
        server.settings = MagicMock()
        server.settings.webhook_domain = "test.com"

        # Создаём app
        app = server.create_app()

        # Создаём запрос
        request = make_mocked_request("GET", "/health")

        # Получаем handler
        handler = None
        for route in app.router.routes():
            if route.resource and route.resource.canonical == "/health":
                handler = route.handler
                break

        assert handler is not None

        # Выполняем handler
        response = await handler(request)

        assert response.status == 200
        # aiohttp Response не имеет метода json(), нужно читать текст
        text = response.text if hasattr(response, "text") else await response.text()
        import json

        data = json.loads(text) if isinstance(text, str) else text
        assert "status" in data or "message" in data

    @pytest.mark.asyncio
    async def test_health_check_metrics_endpoint_healthy(self):
        """Тест health check metrics endpoint (здоровая система)"""
        endpoint = MetricsEndpoint()
        request = MagicMock()

        with patch("bot.database.engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            mock_engine.connect.return_value.__exit__.return_value = None

            with patch("bot.api.metrics_endpoint.get_ai_service") as mock_ai:
                mock_ai.return_value = MagicMock()

                response = await endpoint.health_check(request)
                assert response.status == 200

                import json

                body = response._body if hasattr(response, "_body") else b"{}"
                data = json.loads(body.decode("utf-8"))
                assert data["status"] == "healthy"
                assert data["components"]["database"] == "healthy"
                assert data["components"]["ai_service"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_metrics_endpoint_database_error(self):
        """Тест health check при ошибке БД"""
        endpoint = MetricsEndpoint()
        request = MagicMock()

        with patch("bot.database.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("Database connection failed")

            with patch("bot.api.metrics_endpoint.get_ai_service") as mock_ai:
                mock_ai.return_value = MagicMock()

                response = await endpoint.health_check(request)
                assert response.status == 503

                import json

                body = response._body if hasattr(response, "_body") else b"{}"
                data = json.loads(body.decode("utf-8"))
                assert data["status"] == "degraded"
                assert data["components"]["database"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_metrics_endpoint_ai_unavailable(self):
        """Тест health check при недоступности AI"""
        endpoint = MetricsEndpoint()
        request = MagicMock()

        with patch("bot.database.engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            mock_engine.connect.return_value.__exit__.return_value = None

            with patch("bot.api.metrics_endpoint.get_ai_service") as mock_ai:
                mock_ai.return_value = None

                response = await endpoint.health_check(request)
                assert response.status == 200

                import json

                body = response._body if hasattr(response, "_body") else b"{}"
                data = json.loads(body.decode("utf-8"))
                assert data["components"]["ai_service"] == "unavailable"
