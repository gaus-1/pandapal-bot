"""
Тесты HTTP-only cookie и приёма Bearer/cookie в verify и logout.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.test_utils import make_mocked_request

from bot.api.auth_endpoints import (
    TELEGRAM_SESSION_COOKIE,
    _get_session_token,
    logout,
    telegram_login,
    verify_session,
)


class TestGetSessionToken:
    """Хелпер _get_session_token: cookie или Bearer."""

    def test_returns_from_cookie_first(self):
        req = make_mocked_request(
            "GET", "/api/auth/telegram/verify", headers={"Cookie": f"{TELEGRAM_SESSION_COOKIE}=cookie-token-123"}
        )
        assert _get_session_token(req) == "cookie-token-123"

    def test_returns_from_bearer_when_no_cookie(self):
        req = make_mocked_request(
            "GET", "/api/auth/telegram/verify", headers={"Authorization": "Bearer bearer-token-456"}
        )
        assert _get_session_token(req) == "bearer-token-456"

    def test_returns_none_when_neither(self):
        req = make_mocked_request("GET", "/api/auth/telegram/verify")
        assert _get_session_token(req) is None


class TestLoginSetsCookie:
    """POST login возвращает Set-Cookie и JSON с session_token."""

    @pytest.mark.asyncio
    async def test_login_response_has_set_cookie_and_json_body(self):
        telegram_data = {
            "id": "111",
            "first_name": "Test",
            "last_name": "User",
            "username": "test",
            "auth_date": "1234567890",
            "hash": "will_be_validated",
        }
        req = make_mocked_request(
            "POST",
            "/api/auth/telegram/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        req.post = AsyncMock(return_value=telegram_data)

        with patch(
            "bot.api.auth_endpoints.TelegramAuthService"
        ) as mock_auth_svc, patch("bot.api.auth_endpoints.get_db") as mock_get_db, patch(
            "bot.api.auth_endpoints.get_session_service"
        ) as mock_sess_svc:
            mock_auth_svc.return_value.validate_telegram_auth.return_value = True
            mock_user = type("User", (), {"telegram_id": 111, "full_name": "Test User", "username": "test", "is_premium": False})()
            mock_auth_svc.return_value.get_or_create_user.return_value = mock_user
            mock_sess_svc.return_value.create_session = AsyncMock(return_value="secret-session-token")

            class FakeDB:
                def __enter__(self):
                    return type("DB", (), {"commit": lambda: None})()
                def __exit__(self, *args):
                    pass

            mock_get_db.return_value = FakeDB()

            resp = await telegram_login(req)

        assert resp.status == 200
        set_cookie = resp.headers.get("Set-Cookie", "")
        assert TELEGRAM_SESSION_COOKIE in set_cookie
        assert "HttpOnly" in set_cookie
        assert "secret-session-token" in set_cookie
        body = json.loads(resp.body.decode("utf-8"))
        assert body.get("session_token") == "secret-session-token"
        assert body.get("success") is True


class TestVerifyAndLogoutAcceptCookie:
    """verify и logout принимают токен из cookie (без Bearer)."""

    @pytest.mark.asyncio
    async def test_verify_accepts_cookie(self):
        req = make_mocked_request(
            "GET", "/api/auth/telegram/verify", headers={"Cookie": f"{TELEGRAM_SESSION_COOKIE}=valid-token"}
        )

        mock_session = type(
            "Session",
            (),
            {
                "telegram_id": 999,
                "user_data": {"telegram_id": 999, "full_name": "U", "username": "u", "is_premium": False},
            },
        )()
        mock_user = type(
            "User",
            (),
            {"telegram_id": 999, "full_name": "U", "username": "u", "is_premium": False},
        )()

        with patch("bot.api.auth_endpoints.get_session_service") as mock_sess_svc, patch(
            "bot.api.auth_endpoints.get_db"
        ) as mock_get_db, patch("bot.services.user_service.UserService") as mock_us:
            mock_sess_svc.return_value.get_session = AsyncMock(return_value=mock_session)
            mock_us.return_value.get_user_by_telegram_id.return_value = mock_user

            class Ctx:
                def __enter__(_):
                    return None
                def __exit__(_, *a):
                    pass
            mock_get_db.return_value = Ctx()

            resp = await verify_session(req)

        assert resp.status == 200
        body = json.loads(resp.body.decode("utf-8"))
        assert body.get("success") is True

    @pytest.mark.asyncio
    async def test_logout_accepts_cookie_and_clears_cookie(self):
        req = make_mocked_request(
            "POST", "/api/auth/telegram/logout", headers={"Cookie": f"{TELEGRAM_SESSION_COOKIE}=token-to-delete"}
        )

        with patch("bot.api.auth_endpoints.get_session_service") as mock_sess_svc:
            mock_session = type("Session", (), {"telegram_id": 1})()
            mock_sess_svc.return_value.get_session = AsyncMock(return_value=mock_session)
            mock_sess_svc.return_value.delete_session = AsyncMock(return_value=True)

            resp = await logout(req)

        assert resp.status == 200
        set_cookie = resp.headers.get("Set-Cookie", "")
        assert "Max-Age=0" in set_cookie
        assert TELEGRAM_SESSION_COOKIE in set_cookie
