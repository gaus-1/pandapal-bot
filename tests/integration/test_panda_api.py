"""
Integration тесты для API панды (тамагочи).
Проверяет GET state, POST feed, play, sleep.
"""

import os
import tempfile
from contextlib import contextmanager
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.api.panda_endpoints import setup_panda_routes
from bot.models import Base, User


class TestPandaAPI(AioHTTPTestCase):
    """Тесты для API панды."""

    @classmethod
    def setUpClass(cls):
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix=".db")
        cls.engine = create_engine(f"sqlite:///{cls.db_path}", echo=False)
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        try:
            os.close(cls.db_fd)
            os.unlink(cls.db_path)
        except (PermissionError, OSError):
            pass

    @contextmanager
    def mock_get_db(self):
        db = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    async def get_application(self):
        app = web.Application()
        setup_panda_routes(app)
        return app

    async def setUpAsync(self):
        await super().setUpAsync()
        self.get_db_patcher = patch(
            "bot.api.panda_endpoints.get_db",
            side_effect=lambda: self.mock_get_db(),
        )
        self.get_db_patcher.start()
        self.require_owner_patcher = patch(
            "bot.api.panda_endpoints.require_owner", return_value=None
        )
        self.require_owner_patcher.start()

        self.test_telegram_id = 987654321
        with self.mock_get_db() as db:
            user = User(
                telegram_id=self.test_telegram_id,
                first_name="PandaTest",
                username="pandatest",
                user_type="child",
                age=10,
                grade=5,
            )
            db.add(user)
            db.commit()

    async def tearDownAsync(self):
        from sqlalchemy import delete

        from bot.models import PandaPet

        with self.mock_get_db() as db:
            db.execute(delete(PandaPet).where(PandaPet.user_telegram_id == self.test_telegram_id))
            db.execute(delete(User).where(User.telegram_id == self.test_telegram_id))
            db.commit()
        self.require_owner_patcher.stop()
        self.get_db_patcher.stop()
        await super().tearDownAsync()

    @unittest_run_loop
    async def test_get_panda_state(self):
        """GET state создаёт панду и возвращает состояние."""
        resp = await self.client.request(
            "GET",
            f"/api/miniapp/panda/{self.test_telegram_id}/state",
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is True
        state = data["state"]
        assert "hunger" in state
        assert "mood" in state
        assert "energy" in state
        assert "display_state" in state
        assert "can_feed" in state
        assert "can_play" in state
        assert state["hunger"] == 60
        assert state["mood"] == 70

    @unittest_run_loop
    async def test_panda_feed(self):
        """POST feed увеличивает голод и total_fed_count."""
        resp = await self.client.request(
            "POST",
            f"/api/miniapp/panda/{self.test_telegram_id}/feed",
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is True
        assert data["state"]["total_fed_count"] == 1
        assert data["state"]["hunger"] >= 60

    @unittest_run_loop
    async def test_panda_play(self):
        """POST play увеличивает настроение."""
        resp = await self.client.request(
            "POST",
            f"/api/miniapp/panda/{self.test_telegram_id}/play",
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is True
        assert data["state"]["total_played_count"] == 1

    @unittest_run_loop
    async def test_panda_sleep_need_feed_first(self):
        """POST sleep без предварительного кормления возвращает need_feed_first."""
        resp = await self.client.request(
            "POST",
            f"/api/miniapp/panda/{self.test_telegram_id}/sleep",
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is False
        assert data.get("need_feed_first") is True

    @unittest_run_loop
    async def test_panda_sleep_after_feed(self):
        """POST sleep после кормления успешен."""
        await self.client.request(
            "POST",
            f"/api/miniapp/panda/{self.test_telegram_id}/feed",
        )
        resp = await self.client.request(
            "POST",
            f"/api/miniapp/panda/{self.test_telegram_id}/sleep",
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is True
        assert data["state"]["energy"] == 100
