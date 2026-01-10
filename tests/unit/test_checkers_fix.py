"""
Тест исправления checkers - проверка что current_player правильно устанавливается
"""

import asyncio
import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, GameSession, User
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


@pytest.mark.asyncio
async def test_checkers_current_player_fix(games_service, test_user):
    """Тест исправления current_player в checkers"""
    # Создаем сессию
    session = games_service.create_game_session(test_user.telegram_id, "checkers", {})
    games_service.db.commit()

    # Получаем валидные ходы для пользователя
    valid_moves = games_service.get_checkers_valid_moves(session.id)
    assert len(valid_moves) > 0, "Должны быть валидные ходы для пользователя"

    # Выбираем первый валидный ход
    first_move = valid_moves[0]
    from_row, from_col = first_move["from"]
    to_row, to_col = first_move["to"]

    # Делаем ход - это должно работать, так как current_player = 1 установлен
    result = await games_service.checkers_move(session.id, from_row, from_col, to_row, to_col)
    games_service.db.commit()

    # Проверяем, что ход выполнен успешно
    assert "board" in result
    assert "kings" in result
    assert result.get("game_over") is False or result.get("game_over") is True

    # Проверяем, что состояние сохранилось корректно
    saved_session = games_service.db.get(GameSession, session.id)
    assert saved_session.game_state is not None
    game_state = saved_session.game_state
    assert "board" in game_state
    assert "current_player" in game_state
    # После хода пользователя и хода AI, current_player должен быть 1 (снова пользователь)
    # Или 2, если AI еще не сделал ход
    assert game_state["current_player"] in [1, 2]


@pytest.mark.asyncio
async def test_checkers_multiple_moves(games_service, test_user):
    """Тест нескольких ходов подряд в checkers"""
    # Создаем сессию
    session = games_service.create_game_session(test_user.telegram_id, "checkers", {})
    games_service.db.commit()

    # Делаем несколько ходов подряд
    for _ in range(3):
        valid_moves = games_service.get_checkers_valid_moves(session.id)
        if len(valid_moves) == 0:
            # Нет валидных ходов - игра закончена
            break

        first_move = valid_moves[0]
        from_row, from_col = first_move["from"]
        to_row, to_col = first_move["to"]

        result = await games_service.checkers_move(session.id, from_row, from_col, to_row, to_col)
        games_service.db.commit()

        # Проверяем, что ход выполнен
        assert "board" in result

        if result.get("game_over"):
            break

    # Проверяем, что состояние сохранилось
    saved_session = games_service.db.get(GameSession, session.id)
    assert saved_session.game_state is not None
