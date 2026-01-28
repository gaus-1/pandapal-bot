"""
Сервис игр для PandaPalGo.
Реализует логику игр: крестики-нолики, виселица, 2048.
Включает AI противника (панда) для игры с ребенком.
"""

import random


def _debug_log(
    *,
    hypothesis_id: str,  # noqa: ARG001
    location: str,  # noqa: ARG001
    message: str,  # noqa: ARG001
    data: dict | None = None,  # noqa: ARG001
    run_id: str = "initial",
) -> None:
    """Записать отладочное сообщение в NDJSON-файл debug.log."""
    _ = run_id  # Параметр для совместимости, но не используется
    # Логирование отключено для production
    return


class TicTacToeAI:
    """AI противник для крестиков-ноликов (панда)"""

    def __init__(self, difficulty: str = "medium"):
        """
        Args:
            difficulty: 'easy', 'medium', 'hard'
        """
        self.difficulty = difficulty

    def get_best_move(self, board: list[str | None], player: str) -> int:
        """
        Получить лучший ход для AI.

        Args:
            board: Доска 3x3 (список из 9 элементов: None, 'X', 'O')
            player: Символ AI ('O' для панды)

        Returns:
            int: Индекс клетки для хода
        """
        opponent = "X" if player == "O" else "O"

        if self.difficulty == "easy":
            # Легкий: случайный ход
            available = [i for i in range(9) if board[i] is None]
            return random.choice(available) if available else -1

        elif self.difficulty == "medium":
            # Средний: пытается выиграть, иначе блокирует, иначе стратегический ход
            # 1. Попытка выиграть
            move = self._find_winning_move(board, player)
            if move != -1:
                return move

            # 2. Блокировка противника
            move = self._find_winning_move(board, opponent)
            if move != -1:
                return move

            # 3. Стратегические позиции (углы и центр) - рандомизируем порядок для разнообразия
            strategic_positions = [4, 0, 2, 6, 8, 1, 3, 5, 7]  # Центр, углы, края
            # Перемешиваем стратегические позиции (кроме центра, если он свободен)
            available_strategic = [pos for pos in strategic_positions if board[pos] is None]
            if available_strategic:
                # Если центр свободен, иногда выбираем его, иногда углы
                if 4 in available_strategic and len(available_strategic) > 1:
                    # 70% вероятность выбрать центр, 30% - случайный из доступных
                    if random.random() < 0.7:
                        return 4
                    else:
                        return random.choice([pos for pos in available_strategic if pos != 4])
                return random.choice(available_strategic)

            # 4. Случайный ход (fallback)
            available = [i for i in range(9) if board[i] is None]
            return random.choice(available) if available else -1

        else:  # hard
            # Сложный: minimax алгоритм
            _, move = self._minimax(board, player, True)
            return move

    def _find_winning_move(self, board: list[str | None], player: str) -> int:
        """Найти выигрышный ход"""
        lines = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [0, 3, 6],
            [1, 4, 7],
            [2, 5, 8],
            [0, 4, 8],
            [2, 4, 6],
        ]

        for line in lines:
            values = [board[i] for i in line]
            if values.count(player) == 2 and values.count(None) == 1:
                return line[values.index(None)]

        return -1

    def _minimax(
        self, board: list[str | None], player: str, is_maximizing: bool
    ) -> tuple[int, int]:
        """Minimax алгоритм для оптимальной игры"""
        opponent = "X" if player == "O" else "O"
        winner = self._check_winner(board)

        if winner == player:
            return 1, -1
        elif winner == opponent:
            return -1, -1
        elif self._is_board_full(board):
            return 0, -1

        best_score = -10 if is_maximizing else 10
        best_move = -1

        for i in range(9):
            if board[i] is None:
                board[i] = player if is_maximizing else opponent
                score, _ = self._minimax(board, player, not is_maximizing)
                board[i] = None

                if is_maximizing:
                    if score > best_score:
                        best_score = score
                        best_move = i
                else:
                    if score < best_score:
                        best_score = score
                        best_move = i

        return best_score, best_move

    def _check_winner(self, board: list[str | None]) -> str | None:
        """Проверить победителя"""
        lines = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [0, 3, 6],
            [1, 4, 7],
            [2, 5, 8],
            [0, 4, 8],
            [2, 4, 6],
        ]

        for line in lines:
            values = [board[i] for i in line]
            if values[0] and values[0] == values[1] == values[2]:
                return values[0]

        return None

    def _is_board_full(self, board: list[str | None]) -> bool:
        """Проверить заполнена ли доска"""
        return all(cell is not None for cell in board)


class CheckersAI:
    """AI для шашек (панда)"""

    def get_best_move(
        self, board: list[list[str | None]], player: str
    ) -> tuple[int, int, int, int] | None:
        """
        Получить лучший ход для AI.

        Args:
            board: Доска 8x8 (список списков: None, 'user', 'ai')
            player: Символ AI ('ai')

        Returns:
            Optional[Tuple[int, int, int, int]]: (from_row, from_col, to_row, to_col) или None
        """
        # Ищем все возможные ходы
        moves = self._get_all_moves(board, player)
        if not moves:
            return None

        # Приоритет: взятие фишки > движение вперед > случайный ход
        capture_moves = [m for m in moves if self._is_capture_move(m)]
        if capture_moves:
            return random.choice(capture_moves)

        forward_moves = [m for m in moves if self._is_forward_move(m)]
        if forward_moves:
            return random.choice(forward_moves)

        return random.choice(moves)

    def _get_all_moves(
        self, board: list[list[str | None]], player: str
    ) -> list[tuple[int, int, int, int]]:
        """
        Получить все возможные ходы для игрока.
        DEPRECATED: используется старая логика для обратной совместимости.
        Новая логика в games_service использует CheckersGame.get_valid_moves.
        """
        moves = []
        for row in range(8):
            for col in range(8):
                if board[row][col] == player:
                    moves.extend(self._get_moves_from_position(board, row, col))
        return moves

    def _get_moves_from_position(
        self, board: list[list[str | None]], row: int, col: int
    ) -> list[tuple[int, int, int, int]]:
        """
        Получить все возможные ходы из заданной позиции.
        DEPRECATED: не учитывает дамки и обязательное взятие.
        """
        moves = []
        # AI двигается вниз (увеличение row, так как он вверху доски)
        for dr, dc in [(1, -1), (1, 1)]:
            new_row, new_col = row + dr, col + dc
            if not (0 <= new_row < 8 and 0 <= new_col < 8):
                continue

            if board[new_row][new_col] is None:
                moves.append((row, col, new_row, new_col))
            elif board[new_row][new_col] == "user":
                # Проверяем возможность взятия
                jump_row, jump_col = new_row + dr, new_col + dc
                if 0 <= jump_row < 8 and 0 <= jump_col < 8 and board[jump_row][jump_col] is None:
                    moves.append((row, col, jump_row, jump_col))
        return moves

    def _is_capture_move(self, move: tuple[int, int, int, int]) -> bool:
        """Проверить, является ли ход взятием фишки"""
        from_row, from_col, to_row, to_col = move
        # Если ход на 2 клетки по диагонали - это взятие
        return abs(to_row - from_row) == 2 and abs(to_col - from_col) == 2

    def _is_forward_move(self, move: tuple[int, int, int, int]) -> bool:
        """Проверить, является ли ход движением вперед"""
        from_row, _, to_row, _ = move
        # Для AI (который вверху) движение вперед = движение вниз (увеличение row)
        return to_row > from_row
