"""
Интеграционные тесты API «Моя панда» (panda-pet).
Проверка GET state, POST feed/play/sleep, лимиты, 403 без авторизации.
"""

import os
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from sqlalchemy import create_engine, select
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
        assert data.get("can_climb") is True
        assert data.get("can_fall") is True
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
        assert data["can_feed"] is False  # кулдаун 30 мин

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
    async def test_fall_from_tree_sets_offended_mood(self):
        """POST fall-from-tree понижает mood до offended (≤65) и возвращает состояние."""
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            resp = await self.client.request(
                "POST",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}/fall-from-tree",
                json={},
            )
        assert resp.status == 200
        data = await resp.json()
        assert data["mood"] <= 65

    @unittest_run_loop
    async def test_toilet_cooldown_20_min(self):
        """POST toilet обновляет last_toilet_at, can_toilet False до истечения 20 мин."""
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            resp = await self.client.request(
                "POST",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}/toilet",
                json={},
            )
        assert resp.status == 200
        data = await resp.json()
        assert data["last_toilet_at"] is not None
        assert data["can_toilet"] is False
        assert data["mood"] >= 70

    @unittest_run_loop
    async def test_feed_cooldown_30_min(self):
        """Кормление: первое успешно, второе сразу — 400 (кулдаун 30 мин)."""
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            r1 = await self.client.request(
                "POST",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}/feed",
                json={},
            )
            r2 = await self.client.request(
                "POST",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}/feed",
                json={},
            )
        assert r1.status == 200
        assert r2.status == 400

    @unittest_run_loop
    async def test_climb_cooldown_and_fall_cooldown(self):
        """POST climb устанавливает last_climb_at, can_climb False; POST fall-from-tree — last_fall_at, can_fall False."""
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            resp = await self.client.request(
                "POST",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}/climb",
                json={},
            )
        assert resp.status == 200
        data = await resp.json()
        assert data["last_climb_at"] is not None
        assert data["can_climb"] is False
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            r2 = await self.client.request(
                "POST",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}/climb",
                json={},
            )
        assert r2.status == 400
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            resp = await self.client.request(
                "POST",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}/fall-from-tree",
                json={},
            )
        assert resp.status == 200
        data = await resp.json()
        assert data["last_fall_at"] is not None
        assert data["can_fall"] is False

    @unittest_run_loop
    async def test_get_state_after_24h_absence_returns_offended_mood(self):
        """Если пользователь не заходил в тамагочи 24 ч, при заходе mood понижается до 65 (обиженная панда)."""
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            await self.client.request(
                "GET",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}",
            )
        with self.mock_get_db() as db:
            pet = db.execute(
                select(PandaPet).where(PandaPet.user_telegram_id == self.test_telegram_id)
            ).scalar_one()
            pet.last_opened_at = datetime.now(UTC) - timedelta(hours=25)
            db.commit()
        with patch("bot.api.panda_pet_endpoints.require_owner", return_value=None):
            resp = await self.client.request(
                "GET",
                f"/api/miniapp/panda-pet/{self.test_telegram_id}",
            )
        assert resp.status == 200
        data = await resp.json()
        assert data["mood"] <= 65

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
