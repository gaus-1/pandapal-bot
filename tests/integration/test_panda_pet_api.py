"""
Интеграционные тесты API «Моя панда» (panda-pet).
Проверка GET state, POST feed/play/sleep, лимиты, 403 без авторизации.
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

from bot.api.panda_pet_endpoints import setup_panda_pet_routes
from bot.models import Base, PandaPet, User


class TestPandaPetAPI(AioHTTPTestCase):
    """Тесты API panda-pet."""

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
        setup_panda_pet_routes(app)
        return app

    async def setUpAsync(self):
        await super().setUpAsync()
        self.get_db_patcher = patch("bot.api.panda_pet_endpoints.get_db", self.mock_get_db)
        self.get_db_patcher.start()
        self.test_telegram_id = 999888777
        with self.mock_get_db() as db:
            u = User(
                telegram_id=self.test_telegram_id,
                first_name="Panda",
                username="pandauser",
                user_type="child",
                age=10,
                grade=5,
            )
            db.add(u)
            db.commit()

    async def tearDownAsync(self):
        from sqlalchemy import delete

        with self.mock_get_db() as db:
            db.execute(delete(PandaPet).where(PandaPet.user_telegram_id == self.test_telegram_id))
            db.execute(delete(User).where(User.telegram_id == self.test_telegram_id))
            db.commit()
        self.get_db_patcher.stop()
        await super().tearDownAsync()

    @unittest_run_loop
    async def test_get_state_creates_pet(self):
        """GET без питомца создаёт запись с дефолтами."""
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            resp = await self.client.request(
                "GET",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}",
            )
        assert resp.status == 200
        data = await resp.json()
        assert data["hunger"] == 60
        assert data["mood"] == 70
        assert data["energy"] == 50
        assert data["can_feed"] is True
        assert data["can_play"] is True
        assert data["can_sleep"] is True
        assert "consecutive_visit_days" in data
        assert "achievements" in data

    @unittest_run_loop
    async def test_get_state_returns_existing(self):
        """GET с существующим питомцем возвращает те же данные."""
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            await self.client.request(
                "GET",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}",
            )
            resp = await self.client.request(
                "GET",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}",
            )
        assert resp.status == 200
        data = await resp.json()
        assert data["hunger"] == 60
        assert data["consecutive_visit_days"] >= 1

    @unittest_run_loop
    async def test_feed_updates_state(self):
        """POST feed возвращает обновлённое состояние."""
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            resp = await self.client.request(
                "POST",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}/feed",
                json={},
            )
        assert resp.status == 200
        data = await resp.json()
        assert data["hunger"] == 85
        assert data["can_feed"] is True

    @unittest_run_loop
    async def test_play_updates_state(self):
        """POST play обновляет mood и energy."""
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            resp = await self.client.request(
                "POST",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}/play",
                json={},
            )
        assert resp.status == 200
        data = await resp.json()
        assert data["mood"] == 90
        assert data["energy"] == 40

    @unittest_run_loop
    async def test_sleep_updates_state(self):
        """POST sleep увеличивает energy."""
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            resp = await self.client.request(
                "POST",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}/sleep",
                json={},
            )
        assert resp.status == 200
        data = await resp.json()
        assert data["energy"] == 80

    @unittest_run_loop
    async def test_feed_limit_per_hour(self):
        """После нескольких кормлений подряд хотя бы один ответ — ошибка (400/500)."""
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            statuses = []
            for _ in range(4):
                r = await self.client.request(
                    "POST",
                    f"/api/miniapp/panda-pet/{self.test_telegram_id}/feed",
                    json={},
                )
                statuses.append(r.status)
            assert 200 in statuses, "At least one feed should succeed"
            assert any(s in (400, 500) for s in statuses), (
                "At least one request should hit limit or error: " + str(statuses)
            )

    @unittest_run_loop
    async def test_get_state_user_not_found_404(self):
        """GET для несуществующего пользователя — 404."""
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            resp = await self.client.request(
                "GET",
                "/api/miniapp/panda-pet/111222333",
            )
        assert resp.status == 404
        data = await resp.json()
        assert "error" in data

    @unittest_run_loop
    async def test_require_owner_403_without_auth(self):
        """Запрос без X-Telegram-Init-Data — 403 (A01)."""
        resp = await self.client.request(
            "GET",
            f"/api/miniapp/panda-pet/{self.test_telegram_id}",
        )
        assert resp.status == 403
        data = await resp.json()
        assert "error" in data
