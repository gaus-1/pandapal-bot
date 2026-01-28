"""
Unit тесты для игры шашки
Проверяет логику CheckersGame
"""

import asyncio
import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, GameSession, User
from bot.services.game_engines import CheckersGame
from bot.services.games_service import GamesService


@pytest.fixture(scope="function")
def db_session():
    """Фикстура для реальной БД"""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    engine.dispose()
    try:
        os.close(db_fd)
        os.unlink(db_path)
    except (PermissionError, OSError):
        pass


@pytest.fixture
def test_user(db_session):
    """Создать тестового пользователя"""
    user = User(
        telegram_id=123456789,
        first_name="Test",
        username="testuser",
        user_type="child",
        age=10,
        grade=5,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def games_service(db_session):
    """Фикстура для GamesService"""
    return GamesService(db_session)


class TestCheckersGameEngine:
    """Тесты для CheckersGame engine"""

    def test_game_initialization(self):
        """Инициализация игры"""
        game = CheckersGame()
        assert game.current_player == 1  # Пользователь начинает
        assert game.winner is None
        assert game.must_capture_from is None

        # Проверяем начальную расстановку
        state = game.get_board_state()
        board = state["board"]

        # Черные (AI) должны быть в верхних 3 рядах
        black_count = sum(row.count("ai") for row in board[:3])
        assert black_count == 12  # 3 ряда * 4 клетки в каждом

        # Белые (пользователь) должны быть в нижних 3 рядах
        white_count = sum(row.count("user") for row in board[5:])
        assert white_count == 12

    def test_get_valid_moves_user_start(self):
        """Валидные ходы для пользователя в начале игры"""
        game = CheckersGame()
        valid_moves = game.get_valid_moves(1)  # Игрок 1 (пользователь)

        assert len(valid_moves) > 0
        # Белые могут двигаться только вверх
        for move in valid_moves:
            from_row, from_col = move["from"]
            to_row, to_col = move["to"]
            assert to_row < from_row  # Движение вверх (row уменьшается)

    def test_get_valid_moves_ai_start(self):
        """Валидные ходы для AI в начале игры"""
        game = CheckersGame()
        valid_moves = game.get_valid_moves(2)  # Игрок 2 (AI)

        assert len(valid_moves) > 0
        # Черные могут двигаться только вниз
        for move in valid_moves:
            from_row, from_col = move["from"]
            to_row, to_col = move["to"]
            assert to_row > from_row  # Движение вниз (row увеличивается)

    def test_valid_move(self):
        """Валидный ход"""
        game = CheckersGame()
        valid_moves = game.get_valid_moves(1)

        if valid_moves:
            first_move = valid_moves[0]
            from_row, from_col = first_move["from"]
            to_row, to_col = first_move["to"]

            result = game.make_move(from_row, from_col, to_row, to_col)
            assert result is True
            assert game.current_player == 2  # Ход перешел к AI

    def test_invalid_move(self):
        """Невалидный ход"""
        game = CheckersGame()

        # Пытаемся сделать ход назад (невалидно)
        result = game.make_move(5, 0, 6, 1)  # Движение вниз для белых
        assert result is False

        # Пытаемся сделать ход в занятую клетку
        result = game.make_move(5, 0, 4, 0)  # В пустую клетку на той же колонке
        assert result is False

    def test_capture_move(self):
        """Ход с взятием"""
        game = CheckersGame()

        # Создаем ситуацию для взятия: белая шашка, черная перед ней, пустое поле за ней
        # Белая шашка на (4, 1), черная на (3, 2), пустое поле на (2, 3)
        game.board[4][1] = 1  # Белая
        game.board[3][2] = 2  # Черная (враг)
        game.board[2][3] = 0  # Пустое поле

        # Очищаем остальные фигуры для чистоты теста
        for r in range(8):
            for c in range(8):
                if (r, c) not in [(4, 1), (3, 2), (2, 3)]:
                    game.board[r][c] = 0

        valid_moves = game.get_valid_moves(1)
        capture_moves = [m for m in valid_moves if m["capture"] is not None]

        if capture_moves:
            capture_move = capture_moves[0]
            from_row, from_col = capture_move["from"]
            to_row, to_col = capture_move["to"]
            cap_row, cap_col = capture_move["capture"]

            # До взятия
            assert game.board[cap_row][cap_col] == 2  # Черная фигура есть

            result = game.make_move(from_row, from_col, to_row, to_col)
            assert result is True

            # После взятия черная фигура должна быть удалена
            assert game.board[cap_row][cap_col] == 0
            # Белая фигура должна быть на новом месте
            assert game.board[to_row][to_col] == 1
            # Старое место должно быть пустым
            assert game.board[from_row][from_col] == 0

    def test_king_promotion(self):
        """Превращение в дамку. Ходы только по тёмным клеткам (row+col нечётно)."""
        game = CheckersGame()

        # Белая шашка (1,0), пустое поле (0,1) — оба тёмные
        game.board[1][0] = 1
        game.board[0][1] = 0

        for r in range(8):
            for c in range(8):
                if (r, c) not in [(1, 0), (0, 1)]:
                    game.board[r][c] = 0

        result = game.make_move(1, 0, 0, 1)
        assert result is True
        assert game.board[0][1] == 3  # Дамка

    def test_board_state_format(self):
        """Формат состояния доски"""
        game = CheckersGame()
        state = game.get_board_state()

        assert "board" in state
        assert "kings" in state
        assert "current_player" in state
        assert "winner" in state
        assert "must_capture" in state

        board = state["board"]
        assert len(board) == 8
        assert all(len(row) == 8 for row in board)

        kings = state["kings"]
        assert len(kings) == 8
        assert all(len(row) == 8 for row in kings)


class TestCheckersGameService:
    """Тесты для CheckersGame через GamesService"""

    def test_create_checkers_session(self, games_service, test_user):
        """Создание сессии шашек"""
        session = games_service.create_game_session(test_user.telegram_id, "checkers", {})
        games_service.db.commit()

        assert session.id is not None
        assert session.game_type == "checkers"
        assert session.user_telegram_id == test_user.telegram_id
        assert session.result == "in_progress"

    @pytest.mark.asyncio
    async def test_checkers_valid_move(self, games_service, test_user):
        """Валидный ход в шашках"""
        # Создаем сессию
        session = games_service.create_game_session(test_user.telegram_id, "checkers", {})
        games_service.db.commit()

        # Получаем начальные валидные ходы
        valid_moves = games_service.get_checkers_valid_moves(session.id)
        assert valid_moves is not None
        assert len(valid_moves) > 0

        if valid_moves:
            first_move = valid_moves[0]
            from_pos = first_move["from"]
            to_pos = first_move["to"]

            # Делаем ход
            result = await games_service.checkers_move(
                session.id, from_pos[0], from_pos[1], to_pos[0], to_pos[1]
            )
            games_service.db.commit()

            assert "board" in result
            assert "kings" in result
            assert result.get("game_over") is False or result.get("game_over") is True

    @pytest.mark.asyncio
    async def test_checkers_invalid_move(self, games_service, test_user):
        """Невалидный ход в шашках"""
        session = games_service.create_game_session(test_user.telegram_id, "checkers", {})
        games_service.db.commit()

        # Пытаемся сделать невалидный ход (например, назад)
        with pytest.raises(ValueError, match="Invalid move"):
            await games_service.checkers_move(session.id, 5, 0, 6, 1)

    @pytest.mark.asyncio
    async def test_checkers_game_state_persistence(self, games_service, test_user):
        """Сохранение состояния игры"""
        # Создаем сессию
        session = games_service.create_game_session(test_user.telegram_id, "checkers", {})
        games_service.db.commit()

        # Делаем ход
        valid_moves = games_service.get_checkers_valid_moves(session.id)
        if valid_moves:
            first_move = valid_moves[0]
            from_pos = first_move["from"]
            to_pos = first_move["to"]

            result = await games_service.checkers_move(
                session.id, from_pos[0], from_pos[1], to_pos[0], to_pos[1]
            )
            games_service.db.commit()

            # Проверяем что состояние сохранилось
            saved_session = games_service.db.get(GameSession, session.id)
            assert saved_session.game_state is not None
            assert "board" in saved_session.game_state
            assert "current_player" in saved_session.game_state
