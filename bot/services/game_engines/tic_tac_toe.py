"""
Логика игры крестики-нолики.
"""

from typing import Literal

PlayerType = Literal[1, 2]  # 1 - X, 2 - O


class TicTacToe:
    """Логика игры крестики-нолики"""

    def __init__(self) -> None:
        """Инициализация игры крестики-нолики"""
        self.board: list[list[int | None]] = [[None for _ in range(3)] for _ in range(3)]
        self.current_player: PlayerType = 1  # 1 - X (пользователь), 2 - O (AI)
        self.winner: PlayerType | None = None
        self.is_draw: bool = False
        self.moves_count: int = 0

    def get_state(self) -> dict:
        """Возвращает состояние игры для фронтенда"""
        # Преобразуем в формат для фронтенда: список из 9 элементов
        flat_board = [self.board[i][j] for i in range(3) for j in range(3)]
        # Конвертируем: 1 -> 'X', 2 -> 'O', None -> None
        frontend_board = []
        for cell in flat_board:
            if cell == 1:
                frontend_board.append("X")
            elif cell == 2:
                frontend_board.append("O")
            else:
                frontend_board.append(None)

        return {
            "board": frontend_board,
            "current_player": self.current_player,
            "winner": self.winner,
            "is_draw": self.is_draw,
        }

    def make_move(self, row: int, col: int) -> bool:
        """Сделать ход. Возвращает True, если ход успешен."""
        # Проверка валидности хода
        if not (0 <= row < 3 and 0 <= col < 3):
            return False
        if self.board[row][col] is not None:
            return False
        if self.winner is not None or self.is_draw:
            return False

        # Совершаем ход
        self.board[row][col] = self.current_player
        self.moves_count += 1

        # Проверка победы
        if self._check_win(row, col):
            self.winner = self.current_player
            return True

        # Проверка ничьей
        if self.moves_count == 9:
            self.is_draw = True
            return True

        # Смена хода
        self.current_player = 2 if self.current_player == 1 else 1
        return True

    def _check_win(self, row: int, col: int) -> bool:
        """Проверить победу после хода"""
        player = self.board[row][col]

        # Проверка строки
        if all(self.board[row][c] == player for c in range(3)):
            return True

        # Проверка столбца
        if all(self.board[r][col] == player for r in range(3)):
            return True

        # Проверка главной диагонали
        if row == col and all(self.board[i][i] == player for i in range(3)):
            return True

        # Проверка побочной диагонали
        return row + col == 2 and all(self.board[i][2 - i] == player for i in range(3))

    def reset(self):
        """Сбросить игру"""
        self.__init__()
