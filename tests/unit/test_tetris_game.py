"""
Тесты для TetrisGame.
"""

from bot.services.game_engines import TetrisGame


def test_initial_state_valid():
    """Начальное состояние тетриса корректно и не завершено."""
    game = TetrisGame()
    state = game.get_state()

    assert state["width"] == game.width
    assert state["height"] == game.height
    assert state["score"] == 0
    assert state["lines_cleared"] == 0
    assert state["game_over"] is False


def test_piece_moves_down():
    """Фигура может опускаться вниз и в какой-то момент фиксируется."""
    game = TetrisGame()
    initial_board = [row[:] for row in game.get_state()["board"]]

    # Несколько шагов вниз
    for _ in range(5):
        game.step("down")

    state = game.get_state()
    assert state["board"] != initial_board


def test_complete_line_increases_score():
    """Заполненная линия увеличивает счёт."""
    game = TetrisGame()

    # Заполняем нижнюю строку вручную
    for c in range(game.width):
        game.board[game.height - 1][c] = 1

    # Форсируем фиксацию новой фигуры, чтобы сработало удаление линии
    game._lock_piece()  # type: ignore[protected-access]
    state = game.get_state()

    assert state["lines_cleared"] >= 1
    assert state["score"] >= 100
