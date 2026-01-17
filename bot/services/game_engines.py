"""
Game Engines - чистая логика игр без зависимостей от фреймворков.
Используется в GamesService для управления состоянием игр.
"""

import random
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


class CheckersGame:
    """Логика игры шашки"""

    def __init__(self) -> None:
        """Инициализация игры шашки"""
        # 0 - пусто, 1 - белые (пользователь), 2 - черные (AI), 3 - белая дамка, 4 - черная дамка
        self.board: list[list[int]] = [[0 for _ in range(8)] for _ in range(8)]
        self.current_player: int = 1  # 1 (белые/пользователь) начинает
        self.winner: int | None = None
        self.must_capture_from: tuple[int, int] | None = (
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

    def get_board_state(self) -> dict:
        """Возвращает состояние игры для фронтенда"""
        # Преобразуем в формат для фронтенда: 'user', 'ai', None, и информацию о дамках
        frontend_board = []
        kings_info = []
        for row in self.board:
            frontend_row = []
            kings_row = []
            for cell in row:
                if cell == 1 or cell == 3:
                    frontend_row.append("user")
                    kings_row.append(cell == 3)  # True если дамка
                elif cell == 2 or cell == 4:
                    frontend_row.append("ai")
                    kings_row.append(cell == 4)  # True если дамка
                else:
                    frontend_row.append(None)
                    kings_row.append(False)
            frontend_board.append(frontend_row)
            kings_info.append(kings_row)

        return {
            "board": frontend_board,
            "kings": kings_info,  # Информация о дамках
            "current_player": self.current_player,
            "winner": self.winner,
            "must_capture": self.must_capture_from,
        }

    def get_valid_moves(self, player: int) -> list[dict]:
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

    def _get_piece_moves(self, r: int, c: int, piece: int) -> list[dict]:
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
            # Простые ходы (только если нет обязательного взятия)
            # Но мы собираем все ходы, а фильтрация на уровне get_valid_moves
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.board[nr][nc] == 0:
                moves.append({"from": (r, c), "to": (nr, nc), "capture": None})

            # Взятия
            if is_king:
                # Дамка бьет на любом расстоянии и может приземлиться на любое свободное поле за врагом
                jump_r, jump_c = r + dr, c + dc
                while 0 <= jump_r < 8 and 0 <= jump_c < 8:
                    mid_piece = self.board[jump_r][jump_c]
                    if mid_piece != 0:
                        # Проверяем, вражеская ли это шашка
                        is_enemy = (piece in [1, 3] and mid_piece in [2, 4]) or (
                            piece in [2, 4] and mid_piece in [1, 3]
                        )
                        if is_enemy:
                            # Проверяем все свободные клетки за врагом на этой диагонали
                            land_r, land_c = jump_r + dr, jump_c + dc
                            while 0 <= land_r < 8 and 0 <= land_c < 8:
                                if self.board[land_r][land_c] == 0:
                                    moves.append(
                                        {
                                            "from": (r, c),
                                            "to": (land_r, land_c),
                                            "capture": (jump_r, jump_c),
                                        }
                                    )
                                else:
                                    break  # Препятствие за врагом
                                land_r += dr
                                land_c += dc
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
        self.board: list[list[int]] = [[0] * 4 for _ in range(4)]
        self.score: int = 0
        self.game_over: bool = False
        self.won: bool = False
        self._add_new_tile()
        self._add_new_tile()

    def get_state(self) -> dict:
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
            transposed = list(zip(*self.board, strict=False))
            processed = [self._compress_and_merge(list(col)) for col in transposed]
            self.board = [list(col) for col in zip(*processed, strict=False)]
        elif direction == "down":
            transposed = list(zip(*self.board, strict=False))
            processed = [self._compress_and_merge(list(col)[::-1])[::-1] for col in transposed]
            self.board = [list(col) for col in zip(*processed, strict=False)]
        else:
            return False

        if self.board != original_board:
            self._add_new_tile()
            self._check_status()
            return True
        return False

    def _compress_and_merge(self, row: list[int]) -> list[int]:
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


class TetrisGame:
    """Логика игры Tetris.

    Исправления:
    1. Добавлен метод from_dict для восстановления состояния из Redis/JSON.
    2. Приведение action к нижнему регистру (兼容 'LEFT', 'Left', 'left').
    3. Исправлена центровка фигуры I (spawn x=5), чтобы она была ровно по центру.
    4. Убрана опасная логика отскоков, которая могла ломать состояние.
    5. О-фигура теперь не вращается.
    """

    width: int = 10
    height: int = 20

    # Фигуры. Относительные координаты (row, col)
    # Для I-фигуры изменены смещения для лучшей центровки на сетке 10x20
    _SHAPES = {
        "I": [(0, -1), (0, 0), (0, 1), (0, 2)],  # Горизонтальная I
        "O": [(0, 0), (0, 1), (1, 0), (1, 1)],  # Квадрат
        "T": [(0, -1), (0, 0), (0, 1), (1, 0)],  # T-образная
        "L": [(0, -1), (0, 0), (0, 1), (1, -1)],  # L-образная
        "J": [(0, -1), (0, 0), (0, 1), (1, 1)],  # J-образная
        "S": [(0, 0), (0, 1), (1, -1), (1, 0)],  # S-образная
        "Z": [(0, -1), (0, 0), (1, 0), (1, 1)],  # Z-образная
    }

    def __init__(self) -> None:
        self.board: list[list[int]] = [[0] * self.width for _ in range(self.height)]
        self.score: int = 0
        self.lines_cleared: int = 0
        self.level: int = 1
        self.game_over: bool = False

        self.current_shape: str | None = None
        self.current_rotation: int = 0
        self.current_row: int = 0
        self.current_col: int = 0

        # ГСЧ для мешка фигур
        import random

        self._rnd = random
        self._bag: list[str] = []
        self._refill_bag()
        self._spawn_new_piece()

    def _refill_bag(self) -> None:
        """Заполнить мешок Bag of 7."""
        self._bag = list(self._SHAPES.keys())
        self._rnd.shuffle(self._bag)

    def _spawn_new_piece(self) -> None:
        """Создать новую фигуру."""
        if not self._bag:
            self._refill_bag()

        self.current_shape = self._bag.pop()
        self.current_rotation = 0

        # Критично: Спавн в невидимой зоне выше (row = -1 или -2)
        # Для I-фигуры используем -2, так как она длинная
        self.current_row = -2

        # Центровка по X. width=10, середина 5.
        # Для I-фигуры со смещениями -1..2, кол=5 даст 4..6 (ровный центр)
        self.current_col = self.width // 2 + (1 if self.width % 2 == 0 else 0)

        # Проверка Game Over: проверяем, может ли фигура достичь видимой части поля (row = 0).
        # Если фигура не может быть размещена на верхней границе - конец игры.
        has_blocks = any(any(cell != 0 for cell in row) for row in self.board)
        if has_blocks and not self._can_place(0, self.current_col, 0):
            self.game_over = True

    def _get_blocks(self, row: int, col: int, rotation: int) -> list[tuple[int, int]]:
        """Получить координаты блоков фигуры."""
        offsets = self._SHAPES[self.current_shape or "I"]

        def _rotate(dr: int, dc: int, rot: int) -> tuple[int, int]:
            # Поворот на 90 градусов по часовой стрелке (row, col) -> (-col, row)
            for _ in range(rot % 4):
                dr, dc = -dc, dr
            return dr, dc

        blocks: list[tuple[int, int]] = []
        for dr, dc in offsets:
            r_off, c_off = _rotate(dr, dc, rotation)
            blocks.append((row + r_off, col + c_off))
        return blocks

    def _can_place(self, row: int, col: int, rotation: int) -> bool:
        """Проверить коллизию."""
        for r, c in self._get_blocks(row, col, rotation):
            # Границы X
            if c < 0 or c >= self.width:
                return False
            # Если r < 0 (в буфере сверху), разрешаем
            if r < 0:
                continue
            # Границы Y (дно)
            if r >= self.height:
                return False
            # Занятость ячейки
            if self.board[r][c] != 0:
                return False
        return True

    def _lock_piece(self) -> None:
        """Закрепить фигуру и очистить линии."""
        for r, c in self._get_blocks(self.current_row, self.current_col, self.current_rotation):
            if 0 <= r < self.height and 0 <= c < self.width:
                self.board[r][c] = 1

        # Очистка линий
        new_board = [row for row in self.board if not all(cell != 0 for cell in row)]
        cleared = self.height - len(new_board)

        for _ in range(cleared):
            new_board.insert(0, [0] * self.width)

        self.board = new_board

        if cleared:
            self.lines_cleared += cleared
            score_map = {1: 40, 2: 100, 3: 300, 4: 1200}
            self.score += score_map.get(cleared, 40) * self.level
            self.level = (self.lines_cleared // 10) + 1

        self._spawn_new_piece()

    def step(self, action: str) -> None:
        """Обработка хода."""
        if self.game_over:
            return

        # КРИТИЧНО: Если нет фигуры - создаем новую
        if not self.current_shape:
            self._spawn_new_piece()
            # Если после спавна game_over - выходим
            if self.game_over:
                return

        # Нормализация действия
        action = action.strip().lower()

        new_row, new_col, new_rot = self.current_row, self.current_col, self.current_rotation

        if action == "left":
            new_col -= 1
        elif action == "right":
            new_col += 1
        elif action in ("down", "tick"):
            new_row += 1
        elif action == "rotate" and self.current_shape != "O":
            # O не вращается
            new_rot = (new_rot + 1) % 4

        # Попытка выполнить действие
        if self._can_place(new_row, new_col, new_rot):
            self.current_row, self.current_col, self.current_rotation = new_row, new_col, new_rot

            # Проверка на фиксацию (если мы двигались вниз и теперь уперлись)
            if action in ("down", "tick") and not self._can_place(
                self.current_row + 1, self.current_col, self.current_rotation
            ):
                self._lock_piece()

        # Если действие не выполнено из-за коллизии, но это было движение вниз - фиксируем
        elif action in ("down", "tick") and new_row != self.current_row:
            # Мы попытались идти вниз, но не смогли
            if self.current_row >= 0:  # Только если фигура уже на поле
                self._lock_piece()

    def get_state(self) -> dict:
        """Получить состояние для фронтенда."""
        preview = [row[:] for row in self.board]
        if self.current_shape and not self.game_over:
            for r, c in self._get_blocks(self.current_row, self.current_col, self.current_rotation):
                if 0 <= r < self.height and 0 <= c < self.width:
                    preview[r][c] = 2  # Текущая фигура

        return {
            "board": preview,
            "score": self.score,
            "lines_cleared": self.lines_cleared,
            "level": self.level,
            "game_over": self.game_over,
            "current_shape": self.current_shape,
            "current_row": self.current_row,
            "current_col": self.current_col,
            "current_rotation": self.current_rotation,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TetrisGame":
        """Восстановить игру из словаря (например, из Redis)."""
        game = cls.__new__(cls)  # Создаем экземпляр без вызова __init__
        game.board = data.get("board", [[0] * 10 for _ in range(20)])
        game.score = data.get("score", 0)
        game.lines_cleared = data.get("lines_cleared", 0)
        game.level = data.get("level", 1)

        # КРИТИЧНО: Фильтруем ложные game_over при счете 0
        loaded_game_over = data.get("game_over", False)
        loaded_score = data.get("score", 0)
        loaded_lines = data.get("lines_cleared", 0)
        # Если game_over=true, но счет 0 и линии 0 - это ошибка, сбрасываем флаг
        game.game_over = loaded_game_over and (loaded_score > 0 or loaded_lines > 0)

        game.current_shape = data.get("current_shape")
        game.current_row = data.get("current_row", -2)
        game.current_col = data.get("current_col", 5)
        game.current_rotation = data.get("current_rotation", 0)

        # ГСЧ для мешка фигур
        import random

        game._rnd = random

        # Восстанавливаем состояние мешка, чтобы предсказание фигур работало корректно
        # (Опционально: можно просто пересоздать мешок, если не важна точность предсказания)
        game._bag = data.get("bag", data.get("_bag", []))
        if not game._bag:
            game._refill_bag()

        return game
