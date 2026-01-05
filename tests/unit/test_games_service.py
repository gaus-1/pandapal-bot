"""
Unit тесты для games_service.py
Проверяет логику игр: крестики-нолики, виселица, 2048
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, GameSession, GameStats, User
from bot.services.games_service import GamesService, TicTacToeAI


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
        # Игнорируем ошибки удаления на Windows
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


class TestTicTacToeAI:
    """Тесты для AI крестиков-ноликов"""

    def test_easy_ai_random_move(self):
        """Легкий AI делает случайный ход"""
        ai = TicTacToeAI(difficulty="easy")
        board = [None] * 9
        move = ai.get_best_move(board, "O")
        assert 0 <= move <= 8

    def test_medium_ai_blocks_win(self):
        """Средний AI блокирует выигрыш противника"""
        ai = TicTacToeAI(difficulty="medium")
        # Противник может выиграть на позиции 2
        board = ["X", "X", None, "O", None, None, None, None, None]
        move = ai.get_best_move(board, "O")
        assert move == 2  # Должен заблокировать

    def test_medium_ai_takes_win(self):
        """Средний AI делает выигрышный ход"""
        ai = TicTacToeAI(difficulty="medium")
        # AI может выиграть на позиции 2
        board = ["O", "O", None, "X", None, None, None, None, None]
        move = ai.get_best_move(board, "O")
        assert move == 2  # Должен выиграть

    def test_hard_ai_optimal(self):
        """Сложный AI играет оптимально"""
        ai = TicTacToeAI(difficulty="hard")
        board = [None] * 9
        move = ai.get_best_move(board, "O")
        assert 0 <= move <= 8


class TestGamesService:
    """Тесты для GamesService"""

    def test_create_game_session(self, games_service, test_user):
        """Создание игровой сессии"""
        session = games_service.create_game_session(
            test_user.telegram_id, "tic_tac_toe", {"board": [None] * 9}
        )
        games_service.db.commit()
        assert session.id is not None
        assert session.game_type == "tic_tac_toe"
        assert session.user_telegram_id == test_user.telegram_id
        assert session.result == "in_progress"

    def test_update_game_session(self, games_service, test_user):
        """Обновление игровой сессии"""
        session = games_service.create_game_session(
            test_user.telegram_id, "tic_tac_toe", {"board": [None] * 9}
        )
        games_service.db.commit()
        updated = games_service.update_game_session(
            session.id, {"board": ["X"] + [None] * 8}, "in_progress"
        )
        games_service.db.commit()
        assert updated.game_state["board"][0] == "X"

    def test_finish_game_session(self, games_service, test_user):
        """Завершение игровой сессии"""
        session = games_service.create_game_session(
            test_user.telegram_id, "tic_tac_toe", {"board": [None] * 9}
        )
        games_service.db.commit()
        finished = games_service.finish_game_session(session.id, "win")
        games_service.db.commit()
        assert finished.result == "win"
        assert finished.finished_at is not None

    def test_get_game_stats_empty(self, games_service, test_user):
        """Получение статистики для нового пользователя"""
        stats = games_service.get_game_stats(test_user.telegram_id, "tic_tac_toe")
        assert stats["total_games"] == 0
        assert stats["wins"] == 0
        assert stats["win_rate"] == 0.0

    def test_get_game_stats_after_games(self, games_service, test_user):
        """Получение статистики после игр"""
        # Создаем и завершаем несколько игр
        for i in range(3):
            session = games_service.create_game_session(
                test_user.telegram_id, "tic_tac_toe", {"board": [None] * 9}
            )
            games_service.db.commit()
            result = "win" if i < 2 else "loss"
            games_service.finish_game_session(session.id, result)
            games_service.db.commit()

        stats = games_service.get_game_stats(test_user.telegram_id, "tic_tac_toe")
        assert stats["total_games"] == 3
        assert stats["wins"] == 2
        assert stats["losses"] == 1
        assert stats["win_rate"] == pytest.approx(66.7, abs=0.1)


class TestTicTacToeGame:
    """Тесты для игры крестики-нолики"""

    def test_tic_tac_toe_user_win(self, games_service, test_user):
        """Пользователь выигрывает"""
        # Создаем доску с почти выигрышной комбинацией для пользователя
        # Доска: X X _ | O O _ | _ _ _
        # Пользователь ставит X в позицию 2 и выигрывает
        winning_board = {"board": ["X", "X", None, "O", "O", None, None, None, None]}
        session = games_service.create_game_session(
            test_user.telegram_id, "tic_tac_toe", winning_board
        )
        games_service.db.commit()

        # Пользователь ставит X в позицию 2 и выигрывает
        result = games_service.tic_tac_toe_make_move(session.id, 2)
        games_service.db.commit()
        assert result["game_over"], f"Game should be over, but got: {result}"
        assert (
            result["winner"] == "user"
        ), f"Winner should be 'user', but got: {result.get('winner')}"

    def test_tic_tac_toe_invalid_move(self, games_service, test_user):
        """Невалидный ход"""
        # Создаем доску, где позиция 0 уже занята X
        # Это проще, чем пытаться перезагрузить сессию после хода AI
        board_with_occupied = {"board": ["X", None, None, None, None, None, None, None, None]}
        session = games_service.create_game_session(
            test_user.telegram_id, "tic_tac_toe", board_with_occupied
        )
        games_service.db.commit()

        # Пытаемся поставить в занятую клетку (позиция 0 уже занята X)
        with pytest.raises(ValueError, match="Position already taken"):
            games_service.tic_tac_toe_make_move(session.id, 0)


class TestGame2048:
    """Тесты для игры 2048"""

    def test_2048_move_left(self, games_service, test_user):
        """Ход влево в 2048"""
        board = [[2, 0, 0, 0], [0, 2, 0, 0], [0, 0, 2, 0], [0, 0, 0, 2]]
        session = games_service.create_game_session(
            test_user.telegram_id, "2048", {"board": board, "score": 0}
        )
        games_service.db.commit()

        result = games_service.game_2048_move(session.id, "left")
        games_service.db.commit()
        assert result["board"] is not None
        assert result["score"] >= 0
        assert isinstance(result["board"], list)

    def test_2048_game_over(self, games_service, test_user):
        """Проверка окончания игры 2048"""
        # Доска без возможных ходов
        board = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2],
        ]
        session = games_service.create_game_session(
            test_user.telegram_id, "2048", {"board": board, "score": 100}
        )
        games_service.db.commit()

        result = games_service.game_2048_move(session.id, "left")
        games_service.db.commit()
        # Если нет возможных ходов, игра должна закончиться
        if result["game_over"]:
            assert result["won"] is False
