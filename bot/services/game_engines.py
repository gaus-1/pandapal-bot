"""
Game Engines - чистая логика игр без зависимостей от фреймворков.
Используется в GamesService для управления состоянием игр.
"""

import random
from typing import Dict, List, Literal, Optional, Tuple

PlayerType = Literal[1, 2]  # 1 - X, 2 - O


class TicTacToe:
    """Логика игры крестики-нолики"""

    def __init__(self) -> None:
        """Инициализация игры крестики-нолики"""
        self.board: List[List[Optional[int]]] = [[None for _ in range(3)] for _ in range(3)]
        self.current_player: PlayerType = 1  # 1 - X (пользователь), 2 - O (AI)
        self.winner: Optional[PlayerType] = None
        self.is_draw: bool = False
        self.moves_count: int = 0

    def get_state(self) -> Dict:
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
        if row == col:
            if all(self.board[i][i] == player for i in range(3)):
                return True

        # Проверка побочной диагонали
        if row + col == 2:
            if all(self.board[i][2 - i] == player for i in range(3)):
                return True

        return False

    def reset(self):
        """Сбросить игру"""
        self.__init__()


class CheckersGame:
    """Логика игры шашки"""

    def __init__(self) -> None:
        """Инициализация игры шашки"""
        # 0 - пусто, 1 - белые (пользователь), 2 - черные (AI), 3 - белая дамка, 4 - черная дамка
        self.board: List[List[int]] = [[0 for _ in range(8)] for _ in range(8)]
        self.current_player: int = 1  # 1 (белые/пользователь) начинает
        self.winner: Optional[int] = None
        self.must_capture_from: Optional[Tuple[int, int]] = (
            None  # Координаты шашки, которая должна бить
        )
        self._init_board()

    def _init_board(self):
        """Инициализация доски"""
        for row in range(8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    if row < 3:
                        self.board[row][col] = 2  # Черные (AI) вверху
                    elif row > 4:
                        self.board[row][col] = 1  # Белые (пользователь) внизу

    def get_board_state(self) -> Dict:
        """Возвращает состояние игры для фронтенда"""
        # Преобразуем в формат для фронтенда: 'user', 'ai', None
        frontend_board = []
        for row in self.board:
            frontend_row = []
            for cell in row:
                if cell == 1 or cell == 3:
                    frontend_row.append("user")
                elif cell == 2 or cell == 4:
                    frontend_row.append("ai")
                else:
                    frontend_row.append(None)
            frontend_board.append(frontend_row)

        return {
            "board": frontend_board,
            "current_player": self.current_player,
            "winner": self.winner,
            "must_capture": self.must_capture_from,
        }

    def get_valid_moves(self, player: int) -> List[Dict]:
        """
        Возвращает все возможные ходы для игрока.
        Если есть обязательное взятие, возвращает только его.
        Формат: [{'from': (r, c), 'to': (r, c), 'capture': (r, c) or None}, ...]
        """
        moves = []
        all_captures = []

        # Проходим по всей доске
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == 0:
                    continue

                # Проверяем, принадлежит ли шашка текущему игроку
                is_white = piece == 1 or piece == 3
                is_black = piece == 2 or piece == 4

                if (player == 1 and not is_white) or (player == 2 and not is_black):
                    continue

                # Если есть обязательное взятие, проверяем только эту шашку
                if self.must_capture_from and (r, c) != self.must_capture_from:
                    continue

                piece_moves = self._get_piece_moves(r, c, piece)
                for move in piece_moves:
                    if move["capture"]:
                        all_captures.append(move)
                    else:
                        moves.append(move)

        # Правило обязательного взятия
        if all_captures:
            # Если было начато множественное взятие, игрок обязан продолжать той же шашкой
            if self.must_capture_from:
                return [m for m in all_captures if m["from"] == self.must_capture_from]
            return all_captures

        return moves

    def _get_piece_moves(self, r: int, c: int, piece: int) -> List[Dict]:
        """Получить все возможные ходы для шашки"""
        moves = []
        is_king = piece == 3 or piece == 4
        directions = []

        if piece == 1:  # Белая простая
            directions = [(-1, -1), (-1, 1)]  # Движение вверх
        elif piece == 2:  # Черная простая
            directions = [(1, -1), (1, 1)]  # Движение вниз
        else:  # Дамка
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

        for dr, dc in directions:
            # Простые ходы
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.board[nr][nc] == 0:
                moves.append({"from": (r, c), "to": (nr, nc), "capture": None})

            # Взятия
            if is_king:
                # Дамка бьет на любом расстоянии
                jump_r, jump_c = r + dr, c + dc
                while 0 <= jump_r < 8 and 0 <= jump_c < 8:
                    mid_piece = self.board[jump_r][jump_c]
                    if mid_piece != 0:
                        # Проверяем, вражеская ли это шашка
                        is_enemy = (piece in [1, 3] and mid_piece in [2, 4]) or (
                            piece in [2, 4] and mid_piece in [1, 3]
                        )
                        if is_enemy:
                            # Проверяем клетку за врагом
                            land_r, land_c = jump_r + dr, jump_c + dc
                            if (
                                0 <= land_r < 8
                                and 0 <= land_c < 8
                                and self.board[land_r][land_c] == 0
                            ):
                                moves.append(
                                    {
                                        "from": (r, c),
                                        "to": (land_r, land_c),
                                        "capture": (jump_r, jump_c),
                                    }
                                )
                        break  # Препятствие найдено
                    jump_r += dr
                    jump_c += dc
            else:
                # Простая шашка бьет через 1 клетку
                nr, nc = r + dr * 2, c + dc * 2
                mr, mc = r + dr, c + dc  # Середина
                if 0 <= nr < 8 and 0 <= nc < 8:
                    mid_piece = self.board[mr][mc]
                    is_enemy = (piece == 1 and mid_piece in [2, 4]) or (
                        piece == 2 and mid_piece in [1, 3]
                    )
                    if is_enemy and self.board[nr][nc] == 0:
                        moves.append({"from": (r, c), "to": (nr, nc), "capture": (mr, mc)})

        return moves

    def make_move(self, start_r: int, start_c: int, end_r: int, end_c: int) -> bool:
        """
        Совершает ход. Возвращает True, если ход успешен.
        """
        valid_moves = self.get_valid_moves(self.current_player)
        move_match = None
        for m in valid_moves:
            if m["from"] == (start_r, start_c) and m["to"] == (end_r, end_c):
                move_match = m
                break

        if not move_match:
            return False

        # Перемещение
        piece = self.board[start_r][start_c]
        self.board[start_r][start_c] = 0
        self.board[end_r][end_c] = piece

        # Обработка взятия
        if move_match["capture"]:
            cap_r, cap_c = move_match["capture"]
            self.board[cap_r][cap_c] = 0

            # Превращение в дамку (прерывает серию взятий в некоторых правилах)
            if (piece == 1 and end_r == 0) or (piece == 2 and end_r == 7):
                self.board[end_r][end_c] += 2  # 1->3, 2->4

            # Проверяем, есть ли еще взятия у этой шашки
            new_captures = self._get_piece_moves(end_r, end_c, self.board[end_r][end_c])
            has_next_jump = any(m["capture"] for m in new_captures)

            if has_next_jump:
                self.must_capture_from = (end_r, end_c)
                return True  # Ход переходит снова тому же игроку

        # Превращение в дамку (если не было взятия или если взятие было последним)
        if (piece == 1 and end_r == 0) or (piece == 2 and end_r == 7):
            self.board[end_r][end_c] += 2

        # Смена хода
        self.must_capture_from = None
        self.current_player = 2 if self.current_player == 1 else 1
        self._check_win()
        return True

    def _check_win(self):
        """Проверить победу"""
        opponent = 2 if self.current_player == 1 else 1
        opponent_moves = self.get_valid_moves(opponent)

        # Считаем шашки
        count_1 = sum(row.count(1) + row.count(3) for row in self.board)
        count_2 = sum(row.count(2) + row.count(4) for row in self.board)

        if count_1 == 0:
            self.winner = 2
        elif count_2 == 0:
            self.winner = 1
        elif not opponent_moves:
            self.winner = self.current_player  # Текущий игрок победил


class Game2048:
    """Логика игры 2048"""

    def __init__(self) -> None:
        """Инициализация игры 2048"""
        self.board: List[List[int]] = [[0] * 4 for _ in range(4)]
        self.score: int = 0
        self.game_over: bool = False
        self.won: bool = False
        self._add_new_tile()
        self._add_new_tile()

    def get_state(self) -> Dict:
        """Возвращает состояние игры"""
        return {
            "board": self.board,
            "score": self.score,
            "game_over": self.game_over,
            "won": self.won,
        }

    def _add_new_tile(self):
        """Добавить новую плитку"""
        empty_cells = [(r, c) for r in range(4) for c in range(4) if self.board[r][c] == 0]
        if empty_cells:
            r, c = random.choice(empty_cells)
            self.board[r][c] = 4 if random.random() < 0.1 else 2

    def move(self, direction: str) -> bool:
        """
        direction: 'up', 'down', 'left', 'right'
        Возвращает True, если состояние доски изменилось
        """
        if self.game_over:
            return False

        original_board = [row[:] for row in self.board]

        if direction == "left":
            self.board = [self._compress_and_merge(row) for row in self.board]
        elif direction == "right":
            self.board = [self._compress_and_merge(row[::-1])[::-1] for row in self.board]
        elif direction == "up":
            transposed = list(zip(*self.board))
            processed = [self._compress_and_merge(list(col)) for col in transposed]
            self.board = [list(col) for col in zip(*processed)]
        elif direction == "down":
            transposed = list(zip(*self.board))
            processed = [self._compress_and_merge(list(col)[::-1])[::-1] for col in transposed]
            self.board = [list(col) for col in zip(*processed)]
        else:
            return False

        if self.board != original_board:
            self._add_new_tile()
            self._check_status()
            return True
        return False

    def _compress_and_merge(self, row: List[int]) -> List[int]:
        """Сжать и объединить строку"""
        # 1. Сдвиг влево (удаление нулей)
        new_row = [val for val in row if val != 0]

        # 2. Слияние
        for i in range(len(new_row) - 1):
            if new_row[i] == new_row[i + 1]:
                new_row[i] *= 2
                self.score += new_row[i]
                new_row[i + 1] = 0
                if new_row[i] == 2048:
                    self.won = True  # Победа, но игра может продолжаться

        # 3. Повторный сдвиг влево после слияния
        new_row = [val for val in new_row if val != 0]

        # 4. Дополнение нулями до длины 4
        new_row += [0] * (4 - len(new_row))
        return new_row

    def _check_status(self):
        """Проверить статус игры"""
        # Проверка на наличие пустых ячеек
        for r in range(4):
            for c in range(4):
                if self.board[r][c] == 0:
                    return  # Игра продолжается

        # Проверка на возможность слияния
        for r in range(4):
            for c in range(4):
                current = self.board[r][c]
                # Справа
                if c < 3 and current == self.board[r][c + 1]:
                    return
                # Снизу
                if r < 3 and current == self.board[r + 1][c]:
                    return

        self.game_over = True
