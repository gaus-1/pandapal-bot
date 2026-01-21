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
        next_player = 2 if self.current_player == 1 else 1

        # КРИТИЧНО: Проверяем победу ДО смены хода
        # Проверяем, есть ли у следующего игрока возможные ходы
        next_player_moves = self.get_valid_moves(next_player)

        # Считаем шашки
        count_1 = sum(row.count(1) + row.count(3) for row in self.board)
        count_2 = sum(row.count(2) + row.count(4) for row in self.board)

        # Определяем победителя ПЕРЕД сменой хода
        if count_2 == 0:
            # У черных (AI) не осталось шашек - белые (пользователь) победили
            self.winner = 1
        elif count_1 == 0:
            # У белых (пользователь) не осталось шашек - черные (AI) победили
            self.winner = 2
        elif not next_player_moves:
            # У следующего игрока нет ходов - текущий игрок побеждает
            self.winner = self.current_player

        # Теперь меняем ход (если игра не окончена)
        self.current_player = next_player
        return True

    def _check_win(self):
        """
        УСТАРЕЛ: Проверка победы теперь выполняется в make_move.
        Оставлен для обратной совместимости.
        """
        # Считаем шашки
        count_1 = sum(row.count(1) + row.count(3) for row in self.board)
        count_2 = sum(row.count(2) + row.count(4) for row in self.board)

        if count_1 == 0:
            self.winner = 2
        elif count_2 == 0:
            self.winner = 1
        else:
            # Проверяем наличие ходов у противника
            opponent = 2 if self.current_player == 1 else 1
            opponent_moves = self.get_valid_moves(opponent)
            if not opponent_moves:
                # Противник не может ходить - текущий игрок победил
                # НО: текущий игрок УЖЕ сменился, так что победил предыдущий
                self.winner = opponent  # Побеждает тот, кто только что сходил


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


class TwoDotsGame:
    """Логика игры Two Dots.

    Механика:
    - Сетка цветных точек (8x8)
    - Соединение точек одного цвета (минимум 2)
    - Квадраты - очистка всех точек того же цвета
    - Каскадные эффекты после падения
    - Удаление группы → гравитация → заполнение сверху
    - Подсчет очков
    """

    width: int = 8
    height: int = 8
    num_colors: int = 5  # Количество цветов (1-5)

    def __init__(self) -> None:
        """Инициализация игры Two Dots"""
        self.grid: list[list[int]] = [[0] * self.width for _ in range(self.height)]
        self.score: int = 0
        self.moves_left: int = 30  # Ограничение ходов (опционально)
        self.level: int = 1
        self.game_over: bool = False
        self.selected_path: list[tuple[int, int]] = []  # Текущий выбранный путь
        self._fill_grid()

    def _fill_grid(self) -> None:
        """Заполнить сетку случайными цветами"""
        for r in range(self.height):
            for c in range(self.width):
                self.grid[r][c] = random.randint(1, self.num_colors)

    def _is_adjacent(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> bool:
        """Проверить, являются ли две позиции соседними (горизонтально/вертикально)"""
        r1, c1 = pos1
        r2, c2 = pos2
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def _get_color(self, row: int, col: int) -> int:
        """Получить цвет точки на позиции"""
        if 0 <= row < self.height and 0 <= col < self.width:
            return self.grid[row][col]
        return 0

    def select_dot(self, row: int, col: int) -> bool:
        """Начать выбор с точки. Возвращает True если успешно."""
        if self.game_over:
            return False
        if not (0 <= row < self.height and 0 <= col < self.width):
            return False

        cell = self.grid[row][col]
        # Можно начать с обычной точки или спецточки, но не с пустой
        if cell == 0:
            return False

        self.selected_path = [(row, col)]
        return True

    def add_to_path(self, row: int, col: int) -> bool:
        """Добавить точку в путь. Возвращает True если успешно."""
        if not self.selected_path:
            return False
        if not (0 <= row < self.height and 0 <= col < self.width):
            return False

        # Проверяем, что точка уже не в пути
        if (row, col) in self.selected_path:
            return False

        # Проверяем, что точка соседняя к последней в пути
        last_pos = self.selected_path[-1]
        if not self._is_adjacent(last_pos, (row, col)):
            return False

        # Проверяем, что цвет совпадает (только обычные точки)
        first_color = self._get_color(self.selected_path[0][0], self.selected_path[0][1])
        new_color = self._get_color(row, col)
        if new_color == 0 or new_color != first_color:
            return False

        self.selected_path.append((row, col))
        return True

    def clear_path(self) -> None:
        """Очистить выбранный путь"""
        self.selected_path = []

    def _is_square(self, path: list[tuple[int, int]]) -> bool:
        """Проверить, образует ли путь квадрат (все 4 угла прямоугольника присутствуют)"""
        if len(path) < 4:
            return False

        # Получаем уникальные позиции
        unique_positions = set(path)
        if len(unique_positions) < 4:
            return False

        # Находим границы
        rows = [r for r, _ in unique_positions]
        cols = [c for _, c in unique_positions]
        min_row, max_row = min(rows), max(rows)
        min_col, max_col = min(cols), max(cols)

        width = max_col - min_col + 1
        height = max_row - min_row + 1

        # Прямоугольник должен быть минимум 2x2
        if width < 2 or height < 2:
            return False

        # Проверяем, что все 4 угла прямоугольника присутствуют в пути
        corners = [(min_row, min_col), (min_row, max_col), (max_row, min_col), (max_row, max_col)]

        # Все 4 угла должны быть в пути - это определяет квадрат/прямоугольник
        return all(corner in unique_positions for corner in corners)

    def _remove_all_color(self, color: int) -> int:
        """Удалить все точки указанного цвета. Возвращает количество удаленных."""
        removed = 0
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == color:
                    self.grid[r][c] = 0
                    removed += 1
        return removed

    def _process_cascades(self) -> bool:
        """Обработать каскадные эффекты после падения. Возвращает True если были каскады."""
        had_cascade = False
        max_iterations = 10  # Защита от бесконечного цикла

        for _ in range(max_iterations):
            # Ищем автоматические линии (3+ одинаковых подряд)
            to_remove: set[tuple[int, int]] = set()

            # Проверяем горизонтальные линии
            for r in range(self.height):
                current_color = None
                line_start = 0
                line_length = 0

                for c in range(self.width):
                    color = self.grid[r][c]
                    # Учитываем только обычные цвета (положительные)
                    if color > 0 and color == current_color:
                        line_length += 1
                    else:
                        # Конец линии
                        if current_color is not None and line_length >= 3:
                            # Удаляем линию
                            for cc in range(line_start, line_start + line_length):
                                to_remove.add((r, cc))

                        if color > 0:
                            current_color = color
                            line_start = c
                            line_length = 1
                        else:
                            current_color = None
                            line_start = c + 1
                            line_length = 0

                # Проверяем последнюю линию
                if current_color is not None and line_length >= 3:
                    for cc in range(line_start, line_start + line_length):
                        to_remove.add((r, cc))

            # Проверяем вертикальные линии
            for c in range(self.width):
                current_color = None
                line_start = 0
                line_length = 0

                for r in range(self.height):
                    color = self.grid[r][c]
                    if color > 0 and color == current_color:
                        line_length += 1
                    else:
                        if current_color is not None and line_length >= 3:
                            for rr in range(line_start, line_start + line_length):
                                to_remove.add((rr, c))

                        if color > 0:
                            current_color = color
                            line_start = r
                            line_length = 1
                        else:
                            current_color = None
                            line_start = r + 1
                            line_length = 0

                if current_color is not None and line_length >= 3:
                    for rr in range(line_start, line_start + line_length):
                        to_remove.add((rr, c))

            if not to_remove:
                break

            had_cascade = True
            # Удаляем найденные линии
            for r, c in to_remove:
                self.grid[r][c] = 0

            # Подсчет очков за каскад
            self.score += len(to_remove) * 10

            # Применяем гравитацию
            self._apply_gravity()

            # Заполняем сверху
            self._refill_grid()

        return had_cascade

    def confirm_path(self) -> bool:
        """Подтвердить и удалить выбранный путь. Возвращает True если успешно."""
        if len(self.selected_path) < 2:
            self.clear_path()
            return False

        path_length = len(self.selected_path)
        first_pos = self.selected_path[0]
        first_color = self._get_color(first_pos[0], first_pos[1])
        is_square = self._is_square(self.selected_path)

        # Проверяем квадрат - удаляем все точки того же цвета
        if is_square:
            # Квадрат удаляет все точки того же цвета
            removed = self._remove_all_color(first_color)
            points = removed * 20  # Бонус за квадрат
            self.score += points
        else:
            # Обычное удаление пути
            for r, c in self.selected_path:
                self.grid[r][c] = 0

            # Подсчет очков
            points = path_length * 10
            self.score += points

        # Применяем гравитацию
        self._apply_gravity()

        # Заполняем сверху
        self._refill_grid()

        # Обрабатываем каскады
        self._process_cascades()

        # Уменьшаем ходы
        if self.moves_left > 0:
            self.moves_left -= 1
            if self.moves_left == 0:
                self.game_over = True

        # Проверяем game over (нет валидных ходов)
        if not self._has_valid_moves():
            self.game_over = True

        self.clear_path()
        return True

    def _apply_gravity(self) -> None:
        """Применить гравитацию: точки падают вниз"""
        for c in range(self.width):
            # Собираем все непустые точки в столбце снизу вверх
            column = []
            for r in range(self.height - 1, -1, -1):
                if self.grid[r][c] != 0:
                    column.append(self.grid[r][c])

            # Заполняем столбец снизу
            for r in range(self.height - 1, -1, -1):
                if column:
                    self.grid[r][c] = column.pop(0)
                else:
                    self.grid[r][c] = 0

    def _refill_grid(self) -> None:
        """Заполнить пустые ячейки сверху новыми цветами"""
        for c in range(self.width):
            for r in range(self.height):
                if self.grid[r][c] == 0:
                    self.grid[r][c] = random.randint(1, self.num_colors)

    def _has_valid_moves(self) -> bool:
        """Проверить, есть ли валидные ходы"""
        for r in range(self.height):
            for c in range(self.width):
                color = self.grid[r][c]
                if color == 0:
                    continue

                # Проверяем соседей того же цвета
                neighbors = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
                for nr, nc in neighbors:
                    if (
                        0 <= nr < self.height
                        and 0 <= nc < self.width
                        and self.grid[nr][nc] == color
                    ):
                        return True

        return False

    def get_state(self) -> dict:
        """Получить состояние для фронтенда"""
        return {
            "grid": [row[:] for row in self.grid],
            "score": self.score,
            "moves_left": self.moves_left,
            "level": self.level,
            "game_over": self.game_over,
            "selected_path": self.selected_path[:],
            "width": self.width,
            "height": self.height,
            "num_colors": self.num_colors,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TwoDotsGame":
        """Восстановить игру из словаря"""
        game = cls.__new__(cls)
        game.width = data.get("width", 8)
        game.height = data.get("height", 8)
        game.num_colors = data.get("num_colors", 5)

        loaded_grid = data.get("grid", [[0] * 8 for _ in range(8)])
        # Убеждаемся, что сетка правильного размера
        if len(loaded_grid) != game.height:
            game.grid = [[0] * game.width for _ in range(game.height)]
            game._fill_grid()
        else:
            game.grid = []
            for row in loaded_grid:
                if len(row) == game.width:
                    game.grid.append(row[:])
                else:
                    game.grid.append([0] * game.width)
            # Дополняем если нужно
            while len(game.grid) < game.height:
                game.grid.append([0] * game.width)
            game.grid = game.grid[: game.height]

        game.score = data.get("score", 0)
        game.moves_left = data.get("moves_left", 30)
        game.level = data.get("level", 1)
        game.game_over = data.get("game_over", False)
        game.selected_path = data.get("selected_path", [])

        return game
