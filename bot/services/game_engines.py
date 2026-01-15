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
    """Логика игры Tetris для Mini App.

    Реализация с Bag of 7 для справедливого спавна, Wall Kicks для вращения,
    улучшенной системой очков и корректной очисткой линий.
    """

    width: int = 10
    height: int = 20

    # Фигуры заданы как список относительных координат (row, col)
    _SHAPES = {
        "I": [(0, -1), (0, 0), (0, 1), (0, 2)],
        "O": [(0, 0), (0, 1), (1, 0), (1, 1)],
        "T": [(0, -1), (0, 0), (0, 1), (1, 0)],
        "L": [(0, -1), (0, 0), (0, 1), (1, -1)],
        "J": [(0, -1), (0, 0), (0, 1), (1, 1)],
        "S": [(0, 0), (0, 1), (1, -1), (1, 0)],
        "Z": [(0, -1), (0, 0), (1, 0), (1, 1)],
    }

    def __init__(self) -> None:
        self.board: list[list[int]] = [[0] * self.width for _ in range(self.height)]
        self.score: int = 0
        self.lines_cleared: int = 0
        self.level: int = 1  # УЛУЧШЕНО: Добавлен уровень
        self.game_over: bool = False

        self.current_shape: str | None = None
        self.current_rotation: int = 0
        self.current_row: int = 0
        self.current_col: int = self.width // 2

        # УЛУЧШЕНО: Bag of 7 для справедливого спавна фигур
        import random as _rnd

        self._rnd = _rnd
        self._bag: list[str] = []
        self._refill_bag()

        self._spawn_new_piece()

    def _refill_bag(self) -> None:
        """Заполнить мешок всеми 7 фигурами в случайном порядке (Bag of 7)."""
        self._bag = list(self._SHAPES.keys())
        self._rnd.shuffle(self._bag)

    def _spawn_new_piece(self) -> None:
        """Создать новую фигуру сверху (Bag of 7 алгоритм)."""
        # УЛУЧШЕНО: Используем Bag of 7 для справедливого спавна
        if not self._bag:
            self._refill_bag()

        self.current_shape = self._bag.pop()
        self.current_rotation = 0
        self.current_row = 0
        self.current_col = self.width // 2

        # УЛУЧШЕНО: Проверка Game Over при спавне (как в примере)
        if not self._can_place(self.current_row, self.current_col, self.current_rotation):
            self.game_over = True

    def _get_blocks(self, row: int, col: int, rotation: int) -> list[tuple[int, int]]:
        """Получить координаты блоков фигуры в абсолютных координатах."""
        offsets = self._SHAPES[self.current_shape or "I"]

        def _rotate(dr: int, dc: int, rot: int) -> tuple[int, int]:
            # Поворот на 90 градусов по часовой стрелке rot раз
            for _ in range(rot % 4):
                dr, dc = -dc, dr
            return dr, dc

        blocks: list[tuple[int, int]] = []
        for dr, dc in offsets:
            r_off, c_off = _rotate(dr, dc, rotation)
            blocks.append((row + r_off, col + c_off))
        return blocks

    def _can_place(self, row: int, col: int, rotation: int) -> bool:
        """Проверить, можно ли разместить фигуру в указанной позиции.

        Проверяет:
        1. Границы по X (выход за пределы ширины)
        2. Границы по Y (выход за пределы высоты или достижение дна)
        3. Занятость ячеек (пересечение с уже заполненными блоками)
        """
        for r, c in self._get_blocks(row, col, rotation):
            # Проверка границ по X
            if c < 0 or c >= self.width:
                return False
            # Проверка границ по Y (достижение дна или выход за пределы)
            if r >= self.height:
                return False
            # Проверка занятости (только для валидных координат)
            if r >= 0 and self.board[r][c] != 0:
                return False
        return True

    def _lock_piece(self) -> None:
        """Зафиксировать текущую фигуру на поле и очистить заполненные линии."""
        for r, c in self._get_blocks(self.current_row, self.current_col, self.current_rotation):
            if 0 <= r < self.height and 0 <= c < self.width:
                self.board[r][c] = 1

        # УЛУЧШЕНО: Очистка заполненных линий снизу вверх (как в примере)
        new_board: list[list[int]] = []
        cleared = 0
        # Проходим снизу вверх (от строки height-1 до 0)
        for row_idx in range(self.height - 1, -1, -1):
            row = self.board[row_idx]
            if all(cell != 0 for cell in row):
                # Строка полностью заполнена - удаляем её
                cleared += 1
            else:
                # Строка не полная - сохраняем её
                new_board.insert(0, row)

        # Добавляем пустые строки сверху
        for _ in range(cleared):
            new_board.insert(0, [0] * self.width)

        if cleared:
            self.board = new_board
            self.lines_cleared += cleared

            # УЛУЧШЕНО: Улучшенная система очков с множителями
            # 1 линия = 100, 2 линии = 300, 3 линии = 500, 4 линии = 800
            score_multipliers = {1: 100, 2: 300, 3: 500, 4: 800}
            base_score = score_multipliers.get(cleared, cleared * 100)
            # Умножаем на уровень для дополнительного бонуса
            self.score += base_score * self.level

            # УЛУЧШЕНО: Повышение уровня каждые 10 очищенных линий
            new_level = (self.lines_cleared // 10) + 1
            if new_level > self.level:
                self.level = new_level

        self._spawn_new_piece()

    def step(self, action: str) -> None:
        """Сделать шаг игры.

        Args:
            action: 'left', 'right', 'down', 'rotate', 'tick'
        """
        if self.game_over or not self.current_shape:
            return

        new_row = self.current_row
        new_col = self.current_col
        new_rot = self.current_rotation

        if action == "left":
            new_col -= 1
        elif action == "right":
            new_col += 1
        elif action in ("down", "tick"):
            new_row += 1
        elif action == "rotate":
            new_rot = (new_rot + 1) % 4
            # УЛУЧШЕНО: Wall Kicks - пытаемся сдвинуть фигуру при вращении
            if not self._can_place(new_row, new_col, new_rot):
                # Пробуем сдвинуть влево, вправо, вниз
                kick_offsets = [
                    (0, -1),  # Влево
                    (0, 1),  # Вправо
                    (1, 0),  # Вниз
                    (-1, 0),  # Вверх (редко, но может помочь)
                ]
                kicked = False
                for dr, dc in kick_offsets:
                    if self._can_place(new_row + dr, new_col + dc, new_rot):
                        new_row += dr
                        new_col += dc
                        kicked = True
                        break
                if not kicked:
                    # Вращение невозможно - отменяем
                    new_rot = self.current_rotation

        if self._can_place(new_row, new_col, new_rot):
            self.current_row, self.current_col, self.current_rotation = new_row, new_col, new_rot
            if action in ("down", "tick") and not self._can_place(
                self.current_row + 1, self.current_col, self.current_rotation
            ):
                # Следующий шаг вниз невозможен — фиксируем фигуру
                self._lock_piece()
        elif action in ("down", "tick"):
            # Нельзя пойти вниз — фиксируем фигуру
            self._lock_piece()

    def get_state(self) -> dict:
        """Вернуть состояние для фронтенда."""
        # Копируем поле и накладываем текущую фигуру
        preview = [row[:] for row in self.board]
        if self.current_shape and not self.game_over:
            for r, c in self._get_blocks(self.current_row, self.current_col, self.current_rotation):
                if 0 <= r < self.height and 0 <= c < self.width:
                    preview[r][c] = 2  # 2 = активная фигура

        return {
            "board": preview,
            "score": self.score,
            "lines_cleared": self.lines_cleared,
            "level": self.level,  # УЛУЧШЕНО: Добавлен уровень в состояние
            "game_over": self.game_over,
            "current_shape": self.current_shape,
            "current_row": self.current_row,
            "current_col": self.current_col,
            "current_rotation": self.current_rotation,
            "width": self.width,
            "height": self.height,
        }
