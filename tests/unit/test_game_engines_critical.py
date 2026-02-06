"""
Критичные тесты для игровых движков.

Проверяет исправления:
- Шашки: всегда должны быть возможные ходы или победитель определён
"""

import pytest

from bot.services.game_engines import CheckersGame


class TestCheckersCritical:
    """Критичные тесты для Шашек."""

    def test_checkers_always_has_moves_or_winner(self):
        """
        Проверка что в шашках всегда либо есть возможные ходы, либо определён победитель.
        Не должно быть ситуации 'нет ходов, но игра продолжается'.
        """
        game = CheckersGame()

        # Симулируем 100 случайных ходов
        import random

        for iteration in range(100):
            if game.winner is not None:
                # Игра окончена - проверяем что действительно нет ходов у проигравшего
                loser = 1 if game.winner == 2 else 2
                loser_moves = game.get_valid_moves(loser)
                assert len(loser_moves) == 0, (
                    f"Игра окончена, но у проигравшего ({loser}) есть ходы!"
                )
                break

            current_player = game.current_player
            valid_moves = game.get_valid_moves(current_player)

            # КРИТИЧНО: Всегда должны быть ходы ИЛИ победитель определён
            assert len(valid_moves) > 0 or game.winner is not None, (
                f"Итерация {iteration}: Нет ходов для игрока {current_player}, "
                f"но победитель не определён! Доска:\n{game.board}"
            )

            if len(valid_moves) == 0:
                # Нет ходов - должен быть победитель
                assert game.winner is not None, (
                    f"Итерация {iteration}: Нет ходов, но победитель не определён!"
                )
                break

            # Делаем случайный ход
            move = random.choice(valid_moves)
            success = game.make_move(move["from"][0], move["from"][1], move["to"][0], move["to"][1])
            assert success, f"Итерация {iteration}: Ход не удался, хотя был в списке валидных!"

    def test_checkers_user_can_always_move_or_game_over(self):
        """Проверка что пользователь всегда может сходить или игра окончена."""
        game = CheckersGame()

        for _ in range(50):
            if game.winner is not None:
                break

            # Ход пользователя (белые, player=1)
            if game.current_player == 1:
                user_moves = game.get_valid_moves(1)
                assert len(user_moves) > 0, "Пользователь не может сходить, но игра не окончена!"

                # Делаем первый возможный ход
                move = user_moves[0]
                game.make_move(move["from"][0], move["from"][1], move["to"][0], move["to"][1])

            # Ход AI (черные, player=2)
            else:
                ai_moves = game.get_valid_moves(2)
                if len(ai_moves) == 0:
                    # У AI нет ходов - пользователь должен победить
                    assert game.winner == 1, "У AI нет ходов, но пользователь не победил!"
                    break

                # Делаем случайный ход AI
                import random

                move = random.choice(ai_moves)
                game.make_move(move["from"][0], move["from"][1], move["to"][0], move["to"][1])

    def test_checkers_winner_determined_correctly(self):
        """Проверка что победитель определяется корректно."""
        game = CheckersGame()

        # Симулируем игру до конца
        import random

        for _ in range(200):
            if game.winner is not None:
                break

            valid_moves = game.get_valid_moves(game.current_player)
            if not valid_moves:
                # Нет ходов - должен быть победитель
                assert game.winner is not None, "Нет ходов, но победитель не определён!"
                break

            move = random.choice(valid_moves)
            game.make_move(move["from"][0], move["from"][1], move["to"][0], move["to"][1])

        # Если игра закончилась, проверяем корректность победителя
        if game.winner is not None:
            loser = 1 if game.winner == 2 else 2
            loser_moves = game.get_valid_moves(loser)
            loser_pieces = sum(
                1
                for row in game.board
                for cell in row
                if (loser == 1 and cell in [1, 3]) or (loser == 2 and cell in [2, 4])
            )

            # Проигравший либо не имеет шашек, либо не имеет ходов
            assert loser_pieces == 0 or len(loser_moves) == 0, (
                f"Победитель {game.winner}, но у проигравшего {loser} есть {loser_pieces} шашек "
                f"и {len(loser_moves)} ходов!"
            )

    def test_checkers_capture_obligatory(self):
        """Проверка обязательности взятия."""
        game = CheckersGame()

        # Создаём ситуацию где есть взятие
        game.board = [[0] * 8 for _ in range(8)]
        game.board[5][2] = 1  # Белая шашка пользователя
        game.board[4][3] = 2  # Черная шашка AI (можно срубить)
        game.board[2][4] = 2  # Ещё одна черная (для продолжения игры)
        game.current_player = 1

        valid_moves = game.get_valid_moves(1)

        # Все ходы должны быть взятиями
        assert all(move["capture"] is not None for move in valid_moves), (
            "Когда есть взятие, все ходы должны быть взятиями!"
        )

        # Должно быть хотя бы одно взятие
        assert len(valid_moves) > 0, "Нет доступных взятий, хотя враг рядом!"


class TestGameEnginesRobustness:
    """Тесты устойчивости игровых движков."""

    def test_checkers_handles_edge_cases(self):
        """Проверка что Шашки обрабатывают граничные случаи."""
        game = CheckersGame()

        # Случай 1: Последняя шашка игрока
        game.board = [[0] * 8 for _ in range(8)]
        game.board[7][0] = 1  # Одна белая
        game.board[0][7] = 2  # Одна черная
        game.current_player = 1

        valid_moves = game.get_valid_moves(1)
        # Должен быть хоть один ход или игра окончена
        assert len(valid_moves) > 0 or game.winner is not None

        # Случай 2: Дамка против простой шашки
        game.board = [[0] * 8 for _ in range(8)]
        game.board[3][3] = 3  # Белая дамка
        game.board[5][5] = 2  # Черная простая
        game.current_player = 1

        valid_moves = game.get_valid_moves(1)
        # Дамка должна иметь много ходов
        assert len(valid_moves) > 0, "Дамка должна иметь возможные ходы!"
