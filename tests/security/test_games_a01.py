"""
A01: тесты контроля доступа к игровым сессиям по session_id.

Проверяем, что эндпоинты move/get session/valid-moves возвращают 403,
если запрос без X-Telegram-Init-Data или не от владельца сессии.
"""

import os
import tempfile
from contextlib import contextmanager
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.api.games_endpoints import setup_games_routes
from bot.models import Base, GameSession, User


@contextmanager
def _temp_db_with_game_session():
    """Создаёт временную БД с пользователем и одной игровой сессией (tic_tac_toe)."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        user = User(
            telegram_id=111111111,
            username="owner",
            first_name="Owner",
            last_name="User",
            user_type="child",
            age=10,
            grade=5,
        )
        db.add(user)
        db.flush()
        session = GameSession(
            user_telegram_id=user.telegram_id,
            game_type="tic_tac_toe",
            game_state={"board": ["", "", "", "", "", "", "", "", ""]},
            result=None,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        yield db, session.id
    finally:
        db.close()
        engine.dispose()
        os.close(db_fd)
        os.unlink(db_path)


class TestGamesA01:
    """A01: доступ к игровым сессиям только владельцу."""

    @pytest.mark.asyncio
    async def test_get_game_session_returns_403_without_init_data(self):
        """GET /api/miniapp/games/session/{id} без X-Telegram-Init-Data возвращает 403."""
        with _temp_db_with_game_session() as (db, session_id):
            app = web.Application()
            setup_games_routes(app)

            @contextmanager
            def mock_get_db():
                yield db

            with patch("bot.api.games_endpoints.get_db", mock_get_db):
                async with TestClient(TestServer(app)) as client:
                    resp = await client.get(
                        f"/api/miniapp/games/session/{session_id}",
                        headers={},
                    )
                    assert resp.status == 403, (
                        f"Ожидался 403 без initData, получено {resp.status}"
                    )
                    data = await resp.json()
                    assert "error" in data

    @pytest.mark.asyncio
    async def test_tic_tac_toe_move_returns_403_without_init_data(self):
        """POST .../tic-tac-toe/{id}/move без X-Telegram-Init-Data возвращает 403."""
        with _temp_db_with_game_session() as (db, session_id):
            app = web.Application()
            setup_games_routes(app)

            @contextmanager
            def mock_get_db():
                yield db

            with patch("bot.api.games_endpoints.get_db", mock_get_db):
                async with TestClient(TestServer(app)) as client:
                    resp = await client.post(
                        f"/api/miniapp/games/tic-tac-toe/{session_id}/move",
                        json={"position": 0},
                        headers={"Content-Type": "application/json"},
                    )
                    assert resp.status == 403, (
                        f"Ожидался 403 без initData, получено {resp.status}"
                    )
                    data = await resp.json()
                    assert "error" in data

    @pytest.mark.asyncio
    async def test_get_checkers_valid_moves_returns_403_without_init_data(self):
        """GET .../checkers/{id}/valid-moves без X-Telegram-Init-Data возвращает 403."""
        with _temp_db_with_game_session() as (db, session_id):
            app = web.Application()
            setup_games_routes(app)

            @contextmanager
            def mock_get_db():
                yield db

            with patch("bot.api.games_endpoints.get_db", mock_get_db):
                async with TestClient(TestServer(app)) as client:
                    resp = await client.get(
                        f"/api/miniapp/games/checkers/{session_id}/valid-moves",
                        headers={},
                    )
                    assert resp.status == 403, (
                        f"Ожидался 403 без initData, получено {resp.status}"
                    )
                    data = await resp.json()
                    assert "error" in data

    @pytest.mark.asyncio
    async def test_get_game_session_returns_404_for_unknown_session(self):
        """GET /api/miniapp/games/session/999999: сессия не найдена -> 404."""
        with _temp_db_with_game_session() as (db, _):
            app = web.Application()
            setup_games_routes(app)

            @contextmanager
            def mock_get_db():
                yield db

            with patch("bot.api.games_endpoints.get_db", mock_get_db):
                async with TestClient(TestServer(app)) as client:
                    resp = await client.get(
                        "/api/miniapp/games/session/999999",
                        headers={},
                    )
                    # Сначала загрузка сессии: не найдена -> 404
                    assert resp.status == 404, (
                        f"Для несуществующей сессии ожидался 404, получено {resp.status}"
                    )
