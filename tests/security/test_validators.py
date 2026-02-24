"""
Unit-тесты для bot/api/validators.py.
validate_telegram_id, require_owner, verify_resource_owner (A01) с моком TelegramWebAppAuth.
"""

from unittest.mock import MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from bot.api.validators import (
    require_owner,
    validate_telegram_id,
    verify_resource_owner,
)


class TestValidateTelegramId:
    """Тесты validate_telegram_id из URL path."""

    def test_valid_positive_id(self):
        """Валидные: '123' -> 123."""
        assert validate_telegram_id("123") == 123

    def test_valid_large_id(self):
        """Большой положительный id."""
        assert validate_telegram_id("987654321012345") == 987654321012345

    def test_zero_raises(self):
        """'0' -> ValueError."""
        with pytest.raises(ValueError, match="positive"):
            validate_telegram_id("0")

    def test_negative_raises(self):
        """'-1' -> ValueError."""
        with pytest.raises(ValueError, match="positive"):
            validate_telegram_id("-1")

    def test_non_numeric_raises(self):
        """'abc' -> ValueError."""
        with pytest.raises(ValueError):
            validate_telegram_id("abc")

    def test_empty_string_raises(self):
        """Пустая строка -> ValueError."""
        with pytest.raises(ValueError):
            validate_telegram_id("")


class TestVerifyResourceOwner:
    """Тесты verify_resource_owner и require_owner (A01) с моком TelegramWebAppAuth."""

    def test_no_header_returns_forbidden(self):
        """Нет заголовка X-Telegram-Init-Data -> (False, error_message)."""
        request = make_mocked_request("GET", "/api/miniapp/panda-pet/123")
        allowed, msg = verify_resource_owner(request, 123)
        assert allowed is False
        assert msg is not None
        assert "X-Telegram-Init-Data" in msg or "Authorization" in msg

    def test_no_header_require_owner_returns_403(self):
        """require_owner без заголовка возвращает 403 Response."""
        request = make_mocked_request("GET", "/api/miniapp/panda-pet/123")
        response = require_owner(request, 123)
        assert response is not None
        assert response.status == 403

    @patch("bot.api.validators.TelegramWebAppAuth")
    def test_invalid_init_data_returns_forbidden(self, mock_auth_cls):
        """Невалидный initData (мок возвращает None) -> (False, msg)."""
        mock_auth = MagicMock()
        mock_auth.validate_init_data.return_value = None
        mock_auth_cls.return_value = mock_auth

        request = make_mocked_request(
            "GET",
            "/api/miniapp/panda-pet/123",
            headers={"X-Telegram-Init-Data": "invalid"},
        )
        allowed, msg = verify_resource_owner(request, 123)
        assert allowed is False
        assert "Invalid" in msg or "error" in msg.lower()

    @patch("bot.api.validators.TelegramWebAppAuth")
    def test_wrong_user_id_returns_forbidden(self, mock_auth_cls):
        """requester_id != target_telegram_id -> (False, msg)."""
        mock_auth = MagicMock()
        mock_auth.validate_init_data.return_value = {"user": "data"}
        mock_auth.extract_user_data.return_value = {"id": 999}
        mock_auth_cls.return_value = mock_auth

        request = make_mocked_request(
            "GET",
            "/api/miniapp/panda-pet/123",
            headers={"X-Telegram-Init-Data": "some"},
        )
        allowed, msg = verify_resource_owner(request, 123)
        assert allowed is False
        assert "Access denied" in msg or "denied" in msg.lower()

    @patch("bot.api.validators.TelegramWebAppAuth")
    def test_matching_id_returns_allowed(self, mock_auth_cls):
        """Совпадение id -> (True, None)."""
        mock_auth = MagicMock()
        mock_auth.validate_init_data.return_value = {"user": "data"}
        mock_auth.extract_user_data.return_value = {"id": 123}
        mock_auth_cls.return_value = mock_auth

        request = make_mocked_request(
            "GET",
            "/api/miniapp/panda-pet/123",
            headers={"X-Telegram-Init-Data": "valid"},
        )
        allowed, msg = verify_resource_owner(request, 123)
        assert allowed is True
        assert msg is None

    @patch("bot.api.validators.TelegramWebAppAuth")
    def test_require_owner_matching_id_returns_none(self, mock_auth_cls):
        """require_owner при совпадении id возвращает None (доступ разрешён)."""
        mock_auth = MagicMock()
        mock_auth.validate_init_data.return_value = {"user": "data"}
        mock_auth.extract_user_data.return_value = {"id": 456}
        mock_auth_cls.return_value = mock_auth

        request = make_mocked_request(
            "GET",
            "/api/miniapp/panda-pet/456",
            headers={"X-Telegram-Init-Data": "valid"},
        )
        response = require_owner(request, 456)
        assert response is None
