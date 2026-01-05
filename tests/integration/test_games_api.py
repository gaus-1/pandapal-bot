"""
Integration тесты для API игр
Проверяет полный цикл работы API endpoints
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

from bot.api.games_endpoints import setup_games_routes
from bot.models import Base, User


class TestGamesAPI(AioHTTPTestCase):
    """Тесты для API игр"""

    @classmethod
    def setUpClass(cls):
        """Создать тестовую БД один раз для всех тестов"""
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix=".db")
        cls.engine = create_engine(f"sqlite:///{cls.db_path}", echo=False)
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        """Удалить тестовую БД"""
        cls.engine.dispose()
        try:
            os.close(cls.db_fd)
            os.unlink(cls.db_path)
        except (PermissionError, OSError):
            pass

    @contextmanager
    def mock_get_db(self):
        """Мок для get_db() чтобы использовать тестовую БД"""
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
        """Создать aiohttp приложение для тестов"""
        app = web.Application()
        setup_games_routes(app)
        return app

    async def setUpAsync(self):
        """Настройка перед каждым тестом"""
        await super().setUpAsync()
        # Патчим get_db для использования тестовой БД
        self.get_db_patcher = patch("bot.api.games_endpoints.get_db", self.mock_get_db)
        self.get_db_patcher.start()

        # Создаем тестового пользователя
        self.test_telegram_id = 123456789
        with self.mock_get_db() as db:
            test_user = User(
                telegram_id=self.test_telegram_id,
                first_name="Test",
                username="testuser",
                user_type="child",
                age=10,
                grade=5,
            )
            db.add(test_user)
            db.commit()
            # Сохраняем ID для использования в тестах
            self.test_user_id = test_user.telegram_id

    async def tearDownAsync(self):
        """Очистка после каждого теста"""
        from sqlalchemy import delete

        from bot.models import GameSession, GameStats

        with self.mock_get_db() as db:
            db.execute(
                delete(GameSession).where(GameSession.user_telegram_id == self.test_telegram_id)
            )
            db.execute(delete(GameStats).where(GameStats.user_telegram_id == self.test_telegram_id))
            db.execute(delete(User).where(User.telegram_id == self.test_telegram_id))
            db.commit()

        # Останавливаем патчи
        self.get_db_patcher.stop()
        await super().tearDownAsync()

    @unittest_run_loop
    async def test_create_game_tic_tac_toe(self):
        """Создание игры крестики-нолики"""
        resp = await self.client.request(
            "POST",
            f"/api/miniapp/games/{self.test_telegram_id}/create",
            json={"game_type": "tic_tac_toe"},
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is True
        assert data["game_type"] == "tic_tac_toe"
        assert "session_id" in data
        assert "game_state" in data

    @unittest_run_loop
    async def test_create_game_hangman(self):
        """Создание игры виселица"""
        resp = await self.client.request(
            "POST",
            f"/api/miniapp/games/{self.test_telegram_id}/create",
            json={"game_type": "hangman"},
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is True
        assert data["game_type"] == "hangman"
        assert "word" in data["game_state"]

    @unittest_run_loop
    async def test_create_game_2048(self):
        """Создание игры 2048"""
        resp = await self.client.request(
            "POST",
            f"/api/miniapp/games/{self.test_telegram_id}/create",
            json={"game_type": "2048"},
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is True
        assert data["game_type"] == "2048"
        assert "board" in data["game_state"]

    @unittest_run_loop
    async def test_create_game_invalid_type(self):
        """Создание игры с невалидным типом"""
        resp = await self.client.request(
            "POST",
            f"/api/miniapp/games/{self.test_telegram_id}/create",
            json={"game_type": "invalid_game"},
        )
        assert resp.status == 400

    @unittest_run_loop
    async def test_tic_tac_toe_move(self):
        """Ход в крестики-нолики"""
        # Создаем игру
        create_resp = await self.client.request(
            "POST",
            f"/api/miniapp/games/{self.test_telegram_id}/create",
            json={"game_type": "tic_tac_toe"},
        )
        create_data = await create_resp.json()
        session_id = create_data["session_id"]

        # Делаем ход
        move_resp = await self.client.request(
            "POST",
            f"/api/miniapp/games/tic-tac-toe/{session_id}/move",
            json={"position": 0},
        )
        assert move_resp.status == 200
        move_data = await move_resp.json()
        assert "board" in move_data
        assert move_data["board"][0] == "X"

    @unittest_run_loop
    async def test_hangman_guess(self):
        """Угадывание буквы в виселице"""
        # Создаем игру
        create_resp = await self.client.request(
            "POST",
            f"/api/miniapp/games/{self.test_telegram_id}/create",
            json={"game_type": "hangman"},
        )
        create_data = await create_resp.json()
        session_id = create_data["session_id"]

        # Угадываем букву
        guess_resp = await self.client.request(
            "POST",
            f"/api/miniapp/games/hangman/{session_id}/guess",
            json={"letter": "а"},
        )
        assert guess_resp.status == 200
        guess_data = await guess_resp.json()
        assert "guessed_letters" in guess_data

    @unittest_run_loop
    async def test_2048_move(self):
        """Ход в 2048"""
        # Создаем игру
        create_resp = await self.client.request(
            "POST",
            f"/api/miniapp/games/{self.test_telegram_id}/create",
            json={"game_type": "2048"},
        )
        create_data = await create_resp.json()
        session_id = create_data["session_id"]

        # Делаем ход
        move_resp = await self.client.request(
            "POST",
            f"/api/miniapp/games/2048/{session_id}/move",
            json={"direction": "left"},
        )
        assert move_resp.status == 200
        move_data = await move_resp.json()
        assert "board" in move_data
        assert "score" in move_data

    @unittest_run_loop
    async def test_get_game_session(self):
        """Получение состояния игровой сессии"""
        # Создаем игру
        create_resp = await self.client.request(
            "POST",
            f"/api/miniapp/games/{self.test_telegram_id}/create",
            json={"game_type": "tic_tac_toe"},
        )
        create_data = await create_resp.json()
        session_id = create_data["session_id"]

        # Получаем сессию
        session_resp = await self.client.request("GET", f"/api/miniapp/games/session/{session_id}")
        assert session_resp.status == 200
        session_data = await session_resp.json()
        assert session_data["success"] is True
        assert session_data["session"]["id"] == session_id

    @unittest_run_loop
    async def test_get_game_stats(self):
        """Получение статистики игр"""
        resp = await self.client.request("GET", f"/api/miniapp/games/{self.test_telegram_id}/stats")
        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is True
        assert "stats" in data

    @unittest_run_loop
    async def test_get_game_stats_by_type(self):
        """Получение статистики по типу игры"""
        resp = await self.client.request(
            "GET",
            f"/api/miniapp/games/{self.test_telegram_id}/stats?game_type=tic_tac_toe",
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["success"] is True
