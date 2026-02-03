"""
Интеграционные тесты проактивных сообщений в Mini App.

Проверяют: при GET history с последним user-сообщением старше 24ч
в историю добавляется одно сообщение от панды.
"""

import os
import tempfile
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from aiohttp.test_utils import make_mocked_request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.api.miniapp.other import miniapp_get_chat_history
from bot.models import Base, ChatHistory, User


@pytest.fixture
def real_db_session():
    """Сессия БД (SQLite) для теста."""
    fd, path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{path}", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()
    os.close(fd)
    os.unlink(path)


@pytest.mark.integration
class TestProactiveChatIntegration:
    """Интеграция: GET history с проактивным сообщением."""

    @pytest.mark.asyncio
    async def test_get_history_adds_proactive_after_25h(self, real_db_session):
        """Один user-месседж 25ч назад → GET history добавляет одно ai-сообщение."""
        telegram_id = 999888
        user = User(
            telegram_id=telegram_id,
            username="proactive_test",
            first_name="Test",
            user_type="child",
        )
        real_db_session.add(user)
        real_db_session.commit()

        old_ts = datetime.now(UTC) - timedelta(hours=25)
        msg = ChatHistory(
            user_telegram_id=telegram_id,
            message_text="Пока",
            message_type="user",
            timestamp=old_ts,
        )
        real_db_session.add(msg)
        real_db_session.commit()

        request = make_mocked_request(
            "GET",
            f"/api/miniapp/chat/history/{telegram_id}",
            match_info={"telegram_id": str(telegram_id)},
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
        assert data.get("success") is True
        history = data.get("history", [])
        assert len(history) >= 2
        assert history[0].get("role") == "user"
        assert history[0].get("content") == "Пока"
        assert history[-1].get("role") == "ai"
        assert len(history[-1].get("content", "")) > 5
