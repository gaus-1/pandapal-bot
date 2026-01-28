"""
Детальные тесты логики игровых движков
Проверяет корректность работы CheckersGame, Game2048, TicTacToe
"""

import pytest

from bot.services.game_engines import CheckersGame, Game2048, TicTacToe


class TestCheckersGameDetailed:
    """Детальные тесты для CheckersGame"""

    def test_valid_moves_consistency(self):
        """Проверка консистентности валидных ходов"""
        game = CheckersGame()

        # Получаем валидные ходы для пользователя
        user_moves = game.get_valid_moves(1)
        assert len(user_moves) > 0

        # Проверяем, что все ходы валидны
        for move in user_moves:
            from_pos = move["from"]
            to_pos = move["to"]

            # Проверяем границы
            assert 0 <= from_pos[0] < 8
            assert 0 <= from_pos[1] < 8
            assert 0 <= to_pos[0] < 8
            assert 0 <= to_pos[1] < 8

            # Проверяем формат
            assert isinstance(move["from"], tuple)
            assert isinstance(move["to"], tuple)
            assert move["capture"] is None or isinstance(move["capture"], tuple)

    def test_capture_priority(self):
        """Проверка приоритета взятия"""
        game = CheckersGame()

        # Создаем ситуацию с возможностью взятия
        game.board[5][1] = 1  # Белая
        game.board[4][2] = 2  # Черная (враг)
        game.board[3][3] = 0  # Пустое поле

        # Очищаем остальные фигуры
        for r in range(8):
            for c in range(8):
                if (r, c) not in [(5, 1), (4, 2), (3, 3)]:
                    game.board[r][c] = 0

        valid_moves = game.get_valid_moves(1)

        # Должно быть взятие
        captures = [m for m in valid_moves if m["capture"] is not None]
        assert len(captures) > 0

        # Если есть взятие, должны быть только они
        if captures:
            assert all(m["capture"] is not None for m in valid_moves)

    def test_king_moves(self):
        """Проверка ходов дамки"""
        game = CheckersGame()

        # Создаем дамку
        game.board[3][3] = 3  # Белая дамка

        # Очищаем остальные фигуры
        for r in range(8):
            for c in range(8):
                if (r, c) != (3, 3):
                    game.board[r][c] = 0

        valid_moves = game.get_valid_moves(1)

        # Дамка должна иметь больше ходов, чем простая шашка
        assert len(valid_moves) >= 4  # Дамка может ходить в 4 направления

        # Проверяем, что дамка может ходить в любом направлении
        directions = set()
        for move in valid_moves:
            from_row, from_col = move["from"]
            to_row, to_col = move["to"]
            dr = to_row - from_row
            dc = to_col - from_col
            if dr != 0 and dc != 0:
                directions.add((abs(dr), abs(dc)))

        # Дамка может ходить в любом диагональном направлении
        assert len(directions) > 0

    def test_must_capture_continuation(self):
        """Проверка продолжения множественного взятия. Только тёмные клетки (row+col нечётно)."""
        game = CheckersGame()

        # Белая (5,0), черные (4,1),(2,3), пустые (3,2),(1,4) — все тёмные
        game.board[5][0] = 1
        game.board[4][1] = 2
        game.board[2][3] = 2
        game.board[3][2] = 0
        game.board[1][4] = 0

        for r in range(8):
            for c in range(8):
                if (r, c) not in [(5, 0), (4, 1), (2, 3), (3, 2), (1, 4)]:
                    game.board[r][c] = 0

        result = game.make_move(5, 0, 3, 2)  # бьём (4,1)
        assert result is True

        assert game.must_capture_from is not None
        assert game.must_capture_from == (3, 2)  # шашка приземлилась сюда
        valid_moves = game.get_valid_moves(1)
        assert len(valid_moves) > 0
        assert all(m["from"] == (3, 2) for m in valid_moves)
        assert all(m["capture"] is not None for m in valid_moves)


class TestGame2048Detailed:
    """Детальные тесты для Game2048"""

    def test_move_left_merging(self):
        """Проверка слияния при движении влево"""
        game = Game2048()

        # Создаем доску с возможностью слияния
        game.board = [
            [2, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]

        result = game.move("left")
        assert result is True

        # Должно быть слияние: [2, 2, 0, 0] -> [4, 0, 0, 0]
        assert game.board[0][0] == 4
        assert game.board[0][1] == 0

        # Счет должен увеличиться
        assert game.score >= 4

    def test_move_all_directions(self):
        """Проверка движения во всех направлениях"""
        game = Game2048()

        # Создаем доску с фигурами
        game.board = [
            [2, 0, 0, 0],
            [0, 2, 0, 0],
            [0, 0, 2, 0],
            [0, 0, 0, 2],
        ]

        original_score = game.score

        # Движение влево
        result = game.move("left")
        assert result is True
        assert game.score >= original_score

        # Сброс для следующего теста
        game.board = [
            [0, 0, 0, 2],
            [0, 0, 2, 0],
            [0, 2, 0, 0],
            [2, 0, 0, 0],
        ]

        # Движение вправо
        result = game.move("right")
        assert result is True

        # Движение вверх
        game.board = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [2, 0, 0, 0],
            [2, 0, 0, 0],
        ]

        result = game.move("up")
        assert result is True
        assert game.board[0][0] == 4 or game.board[1][0] == 2

    def test_game_over_detection(self):
        """Проверка обнаружения окончания игры"""
        game = Game2048()

        # Создаем доску без возможных ходов
        game.board = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2],
        ]

        # Пытаемся сделать ход - должен не измениться
        result = game.move("left")
        assert result is False

        # Проверяем статус
        game._check_status()
        assert game.game_over is True

    def test_win_condition(self):
        """Проверка условия победы (2048)"""
        game = Game2048()

        # Создаем доску с возможностью слияния до 2048
        game.board = [
            [1024, 1024, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]

        # Делаем ход, который создает 2048
        result = game.move("left")
        assert result is True

        # Проверяем, что 2048 создано и won установлен
        assert game.won is True
        assert 2048 in [cell for row in game.board for cell in row]

    def test_new_tile_generation(self):
        """Проверка генерации новой плитки"""
        game = Game2048()

        # Очищаем доску
        for r in range(4):
            for c in range(4):
                game.board[r][c] = 0

        # Добавляем одну плитку
        game.board[0][0] = 2

        # Делаем ход (не должно измениться, но может добавиться плитка)
        original_empty = sum(row.count(0) for row in game.board)

        game._add_new_tile()

        # Должна добавиться новая плитка
        new_empty = sum(row.count(0) for row in game.board)
        assert new_empty < original_empty


class TestTicTacToeDetailed:
    """Детальные тесты для TicTacToe"""

    def test_horizontal_win(self):
        """Проверка выигрыша по горизонтали"""
        game = TicTacToe()

        # Пользователь ставит X в первую строку
        game.make_move(0, 0)  # X
        assert game.current_player == 2  # Переход к AI
        game.make_move(1, 0)  # O (AI)
        assert game.current_player == 1  # Переход к пользователю
        game.make_move(0, 1)  # X
        assert game.current_player == 2  # Переход к AI
        game.make_move(1, 1)  # O (AI)
        assert game.current_player == 1  # Переход к пользователю
        result = game.make_move(0, 2)  # X - выигрыш

        assert result is True
        assert game.winner == 1
        # После выигрыша current_player не меняется (игра закончена)
        assert game.current_player == 1

    def test_vertical_win(self):
        """Проверка выигрыша по вертикали"""
        game = TicTacToe()

        # Пользователь ставит X в первый столбец
        game.make_move(0, 0)  # X
        game.make_move(0, 1)  # O (AI)
        game.make_move(1, 0)  # X
        game.make_move(0, 2)  # O (AI)
        game.make_move(2, 0)  # X - выигрыш

        assert game.winner == 1

    def test_diagonal_win(self):
        """Проверка выигрыша по диагонали"""
        game = TicTacToe()

        # Пользователь ставит X по диагонали
        game.make_move(0, 0)  # X
        game.make_move(0, 1)  # O (AI)
        game.make_move(1, 1)  # X
        game.make_move(0, 2)  # O (AI)
        game.make_move(2, 2)  # X - выигрыш

        assert game.winner == 1

    def test_draw_detection(self):
        """Проверка обнаружения ничьей"""
        game = TicTacToe()

        # Заполняем доску без выигрыша
        game.make_move(0, 0)  # X
        game.make_move(0, 1)  # O
        game.make_move(0, 2)  # X
        game.make_move(1, 0)  # O
        game.make_move(1, 2)  # X
        game.make_move(1, 1)  # O
        game.make_move(2, 0)  # X
        game.make_move(2, 2)  # O
        game.make_move(2, 1)  # X - ничья

        assert game.is_draw is True
        assert game.winner is None

    def test_invalid_move_protection(self):
        """Проверка защиты от невалидных ходов"""
        game = TicTacToe()

        # Пытаемся поставить в занятую клетку
        game.make_move(0, 0)  # X
        result = game.make_move(0, 0)  # X снова
        assert result is False

        # Пытаемся поставить вне доски
        result = game.make_move(-1, 0)
        assert result is False

        result = game.make_move(3, 0)
        assert result is False

    def test_state_persistence_format(self):
        """Проверка формата сохранения состояния"""
        game = TicTacToe()

        # Делаем несколько ходов
        game.make_move(0, 0)
        game.make_move(0, 1)

        state = game.get_state()

        assert "board" in state
        assert "current_player" in state
        assert "winner" in state
        assert "is_draw" in state

        board = state["board"]
        assert len(board) == 9
        assert all(cell in [None, "X", "O"] for cell in board)
