"""
Тесты доступа к GET /api/auth/stats.

Endpoint должен возвращать 403 при запросе не с localhost и без валидного X-Internal-Monitor.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.test_utils import make_mocked_request

from bot.api.auth_endpoints import (
    AUTH_STATS_ALLOWED_IPS,
    _is_auth_stats_allowed,
    session_stats,
)


class TestAuthStatsAccess:
    """Доступ к /api/auth/stats только с localhost или с секретом."""

    def test_is_allowed_from_localhost_ipv4(self):
        req = make_mocked_request("GET", "/api/auth/stats")
        type(req).remote = property(lambda self: "127.0.0.1")
        assert _is_auth_stats_allowed(req) is True

    def test_is_allowed_from_localhost_ipv6(self):
        req = make_mocked_request("GET", "/api/auth/stats")
        type(req).remote = property(lambda self: "::1")
        assert _is_auth_stats_allowed(req) is True

    def test_is_forbidden_from_external_ip(self):
        req = make_mocked_request("GET", "/api/auth/stats")
        type(req).remote = property(lambda self: "192.168.1.100")
        assert _is_auth_stats_allowed(req) is False

    def test_is_forbidden_from_public_ip(self):
        req = make_mocked_request("GET", "/api/auth/stats")
        type(req).remote = property(lambda self: "8.8.8.8")
        assert _is_auth_stats_allowed(req) is False

    @pytest.mark.asyncio
    async def test_session_stats_returns_403_for_external_ip(self):
        req = make_mocked_request("GET", "/api/auth/stats")
        type(req).remote = property(lambda self: "10.0.0.5")
        resp = await session_stats(req)
        assert resp.status == 403
        raw = resp.body if resp.body else b"{}"
        body = json.loads(raw.decode("utf-8"))
        assert body.get("error") == "Forbidden"

    @pytest.mark.asyncio
    async def test_session_stats_returns_200_for_localhost(self):
        req = make_mocked_request("GET", "/api/auth/stats")
        type(req).remote = property(lambda self: "127.0.0.1")
        with patch(
            "bot.api.auth_endpoints.get_session_service",
            return_value=AsyncMock(get_stats=AsyncMock(return_value={"total_sessions": 0})),
        ):
            resp = await session_stats(req)
        assert resp.status == 200
        raw = resp.body if resp.body else b"{}"
        body = json.loads(raw.decode("utf-8"))
        assert body.get("success") is True
        assert "stats" in body

    def test_default_allowed_ips_contains_localhost(self):
        assert "127.0.0.1" in AUTH_STATS_ALLOWED_IPS
        assert "::1" in AUTH_STATS_ALLOWED_IPS
