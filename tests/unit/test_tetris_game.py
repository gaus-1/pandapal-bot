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
    assert state["level"] == 1
    assert state["game_over"] is False
    assert "bag" in state or hasattr(game, "_bag")


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
    # Стандартная система очков: 1 линия = 40 * Level (при Level=1 это 40)
    assert state["score"] >= 40


def test_bag_of_7_spawn():
    """Bag of 7 гарантирует справедливый спавн всех фигур."""
    game = TetrisGame()

    # Собираем все фигуры из мешка
    spawned_shapes = []
    for _ in range(7):
        shape = game.current_shape
        spawned_shapes.append(shape)
        # Фиксируем фигуру чтобы спавнить следующую
        game._lock_piece()  # type: ignore[protected-access]

    # Проверяем, что все 7 фигур были спавнены
    unique_shapes = set(spawned_shapes)
    assert len(unique_shapes) == 7, f"Ожидалось 7 уникальных фигур, получено {len(unique_shapes)}"


def test_wall_kicks_on_rotation():
    """Wall Kicks позволяют вращать фигуру даже у стены."""
    game = TetrisGame()

    # Перемещаем фигуру к правой стене
    for _ in range(5):
        game.step("right")

    # Пытаемся вращать - должно сработать с wall kick
    initial_rotation = game.current_rotation
    game.step("rotate")

    # Вращение должно произойти (возможно со сдвигом)
    assert game.current_rotation != initial_rotation or game.current_col < 5


def test_level_increases_with_lines():
    """Уровень повышается каждые 10 очищенных линий."""
    game = TetrisGame()

    # Заполняем и очищаем линии
    for line_idx in range(10):
        # Заполняем строку
        for c in range(game.width):
            game.board[game.height - 1 - line_idx][c] = 1
        # Очищаем линию
        game._lock_piece()  # type: ignore[protected-access]

    state = game.get_state()
    assert state["level"] >= 2, f"Ожидался уровень >= 2, получен {state['level']}"


def test_score_multipliers():
    """Система очков использует множители за несколько линий."""
    game = TetrisGame()

    # Заполняем 2 линии
    for line_idx in range(2):
        for c in range(game.width):
            game.board[game.height - 1 - line_idx][c] = 1

    initial_score = game.score
    game._lock_piece()  # type: ignore[protected-access]

    state = game.get_state()
    # Стандартная система очков: 2 линии = 100 * Level (при Level=1 это 100)
    assert state["score"] > initial_score + 50  # Минимум 100 очков за 2 линии


def test_line_clearing_bottom_up():
    """Очистка линий происходит снизу вверх."""
    game = TetrisGame()

    # Заполняем 2 линии: нижнюю и предпоследнюю
    for line_idx in range(2):
        for c in range(game.width):
            game.board[game.height - 1 - line_idx][c] = 1

    # Сохраняем состояние до очистки
    lines_before = sum(1 for row in game.board if all(cell != 0 for cell in row))

    game._lock_piece()  # type: ignore[protected-access]

    # Проверяем, что обе линии очищены
    lines_after = sum(1 for row in game.board if all(cell != 0 for cell in row))
    assert lines_after < lines_before


def test_game_over_on_spawn_collision():
    """Game Over происходит при блокировке спавна."""
    game = TetrisGame()

    # Заполняем верхние строки НЕ полностью, чтобы они не очистились
    # Фигуры спавнятся в центре (col=5), занимая ячейки примерно от col=3 до col=7
    # Заполняем эти позиции в строках 0-2, оставляя другие пустыми (чтобы линии не очистились)
    for r in range(3):
        for c in range(3, 8):  # Центральные колонки где спавнятся фигуры
            game.board[r][c] = 1

    # Убираем текущую фигуру, чтобы она не блокировалась в неправильном месте
    # При _lock_piece текущая фигура будет заблокирована (но она вне доски),
    # линии не очистятся (т.к. они не полные), затем спавнится новая фигура
    # Новая фигура не сможет быть размещена из-за заполненных ячеек в центре
    game._lock_piece()  # type: ignore[protected-access]

    assert game.game_over, "Ожидался Game Over при блокировке спавна"


def test_piece_spawns_at_top():
    """Фигура спавнится на верхней границе поля (row = 0) и не завершает игру."""
    game = TetrisGame()

    # Проверяем начальное состояние
    assert game.current_row == 0, "Фигура должна спавниться на row = 0"
    assert game.game_over is False, "Игра не должна быть завершена при спавне"

    # Проверяем, что фигура может быть размещена на верхней границе
    assert game._can_place(0, game.current_col, game.current_rotation), \
        "Фигура должна быть размещена на верхней границе поля"


def test_first_move_down_does_not_end_game():
    """Первое движение вниз не должно завершать игру."""
    game = TetrisGame()

    # Проверяем начальное состояние
    initial_row = game.current_row
    assert initial_row == 0, "Фигура должна быть на row = 0"
    assert game.game_over is False, "Игра не должна быть завершена"

    # Делаем первое движение вниз
    game.step("down")

    # Фигура должна переместиться вниз, но игра не должна завершиться
    assert game.current_row == 1, "Фигура должна переместиться на row = 1"
    assert game.game_over is False, "Игра не должна завершиться после первого движения"

    # Делаем еще несколько движений вниз
    for _ in range(3):
        game.step("down")

    # Фигура должна переместиться дальше вниз, но игра все еще не должна завершиться
    assert game.current_row > 1, "Фигура должна переместиться дальше вниз"
    assert game.game_over is False, "Игра не должна завершиться пока фигура не зафиксирована"
