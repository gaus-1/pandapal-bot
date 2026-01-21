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


class EruditeGame:
    """Логика игры Эрудит (Scrabble).

    Механика:
    - Поле 15x15 клеток с бонусными клетками
    - Фишки с буквами и очками
    - Составление слов по правилам кроссворда
    - Подсчет очков с учетом бонусов
    - AI противник
    """

    BOARD_SIZE: int = 15
    TILES_PER_PLAYER: int = 7
    BONUS_ALL_TILES: int = 50  # Бонус за использование всех 7 фишек

    # Распределение букв и очков (русский Эрудит)
    LETTER_VALUES: dict[str, int] = {
        "А": 1,
        "Б": 3,
        "В": 1,
        "Г": 3,
        "Д": 2,
        "Е": 1,
        "Ж": 5,
        "З": 5,
        "И": 1,
        "Й": 4,
        "К": 2,
        "Л": 2,
        "М": 2,
        "Н": 1,
        "О": 1,
        "П": 2,
        "Р": 1,
        "С": 1,
        "Т": 1,
        "У": 2,
        "Ф": 8,
        "Х": 5,
        "Ц": 5,
        "Ч": 5,
        "Ш": 8,
        "Щ": 10,
        "Ъ": 15,
        "Ы": 4,
        "Ь": 3,
        "Э": 8,
        "Ю": 8,
        "Я": 3,
        "*": 0,  # Звездочка (джокер)
    }

    LETTER_COUNTS: dict[str, int] = {
        "А": 8,
        "Б": 2,
        "В": 4,
        "Г": 2,
        "Д": 4,
        "Е": 9,
        "Ж": 1,
        "З": 2,
        "И": 6,
        "Й": 1,
        "К": 4,
        "Л": 4,
        "М": 3,
        "Н": 5,
        "О": 10,
        "П": 4,
        "Р": 5,
        "С": 5,
        "Т": 5,
        "У": 4,
        "Ф": 1,
        "Х": 1,
        "Ц": 1,
        "Ч": 1,
        "Ш": 1,
        "Щ": 1,
        "Ъ": 1,
        "Ы": 2,
        "Ь": 2,
        "Э": 1,
        "Ю": 1,
        "Я": 2,
        "*": 3,  # Звездочки
    }

    # Бонусные клетки (0=обычная, 1=бонус буквы x2, 2=x3, 3=бонус слова x2, 4=x3)
    # Центральная клетка (7,7) - стартовая, бонус слова x2
    def __init__(self) -> None:
        """Инициализация игры Эрудит"""
        # Поле: None = пусто, str = буква
        self.board: list[list[str | None]] = [
            [None] * self.BOARD_SIZE for _ in range(self.BOARD_SIZE)
        ]

        # Бонусные клетки (0=обычная, 1=буква x2, 2=буква x3, 3=слово x2, 4=слово x3)
        self.bonus_cells: list[list[int]] = [[0] * self.BOARD_SIZE for _ in range(self.BOARD_SIZE)]
        self._init_bonus_cells()

        # Мешок с фишками
        self.bag: list[str] = []
        self._init_bag()

        # Фишки игроков
        self.player_tiles: list[str] = []
        self.ai_tiles: list[str] = []
        self._deal_tiles()

        # Счет
        self.player_score: int = 0
        self.ai_score: int = 0

        # Состояние игры
        self.current_player: int = 1  # 1 = игрок, 2 = AI
        self.game_over: bool = False
        self.first_move: bool = True  # Первый ход должен проходить через центр
        self.passes_count: int = 0  # Счетчик пропусков подряд

        # Текущий ход (для валидации)
        self.current_move: list[tuple[int, int, str]] = []  # [(row, col, letter), ...]

        # Загружаем словарь
        from bot.services.erudite_dictionary import is_valid_word

        self.is_valid_word = is_valid_word

    def _init_bonus_cells(self) -> None:
        """Инициализация бонусных клеток (стандартная раскладка Scrabble)"""
        # Бонусы слова x3 (красные углы)
        for r, c in [(0, 0), (0, 7), (0, 14), (7, 0), (7, 14), (14, 0), (14, 7), (14, 14)]:
            self.bonus_cells[r][c] = 4  # x3 слова

        # Бонусы слова x2 (розовые)
        for r, c in [
            (1, 1),
            (1, 13),
            (2, 2),
            (2, 12),
            (3, 3),
            (3, 11),
            (4, 4),
            (4, 10),
            (10, 4),
            (10, 10),
            (11, 3),
            (11, 11),
            (12, 2),
            (12, 12),
            (13, 1),
            (13, 13),
            (7, 7),  # Центр - стартовая клетка
        ]:
            self.bonus_cells[r][c] = 3  # x2 слова

        # Бонусы буквы x2 (светло-синие)
        for r, c in [
            (0, 3),
            (0, 11),
            (2, 6),
            (2, 8),
            (3, 0),
            (3, 7),
            (3, 14),
            (6, 2),
            (6, 6),
            (6, 8),
            (6, 12),
            (7, 3),
            (7, 11),
            (8, 2),
            (8, 6),
            (8, 8),
            (8, 12),
            (11, 0),
            (11, 7),
            (11, 14),
            (12, 6),
            (12, 8),
            (14, 3),
            (14, 11),
        ]:
            self.bonus_cells[r][c] = 1  # x2 буквы

        # Бонусы буквы x3 (темно-синие)
        for r, c in [
            (1, 5),
            (1, 9),
            (5, 1),
            (5, 5),
            (5, 9),
            (5, 13),
            (9, 1),
            (9, 5),
            (9, 9),
            (9, 13),
            (13, 5),
            (13, 9),
        ]:
            self.bonus_cells[r][c] = 2  # x3 буквы

    def _init_bag(self) -> None:
        """Инициализация мешка с фишками"""
        self.bag = []
        for letter, count in self.LETTER_COUNTS.items():
            self.bag.extend([letter] * count)
        random.shuffle(self.bag)

    def _deal_tiles(self) -> None:
        """Раздать фишки игрокам"""
        self.player_tiles = [
            self.bag.pop() for _ in range(min(self.TILES_PER_PLAYER, len(self.bag)))
        ]
        self.ai_tiles = [self.bag.pop() for _ in range(min(self.TILES_PER_PLAYER, len(self.bag)))]

    def place_tile(self, row: int, col: int, letter: str) -> bool:
        """Разместить фишку на поле (для текущего хода)."""
        if not (0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE):
            return False
        if self.board[row][col] is not None:
            return False  # Клетка уже занята

        tiles = self.player_tiles if self.current_player == 1 else self.ai_tiles
        if letter not in tiles:
            return False  # Нет такой фишки

        self.current_move.append((row, col, letter))
        return True

    def clear_move(self) -> None:
        """Очистить текущий ход"""
        self.current_move = []

    def validate_move(self) -> tuple[bool, str]:
        """Валидировать текущий ход. Возвращает (успех, сообщение об ошибке)."""
        if not self.current_move:
            return False, "Ход пустой"

        # Проверка: все фишки на одной линии (горизонталь или вертикаль)
        rows = [r for r, _, _ in self.current_move]
        cols = [c for _, c, _ in self.current_move]

        is_horizontal = len(set(rows)) == 1
        is_vertical = len(set(cols)) == 1

        if not (is_horizontal or is_vertical):
            return False, "Фишки должны быть на одной линии"

        # Проверка: фишки соседние
        if is_horizontal:
            sorted_cols = sorted(cols)
            for i in range(len(sorted_cols) - 1):
                if sorted_cols[i + 1] - sorted_cols[i] != 1:
                    return False, "Фишки должны быть соседними"
        else:
            sorted_rows = sorted(rows)
            for i in range(len(sorted_rows) - 1):
                if sorted_rows[i + 1] - sorted_rows[i] != 1:
                    return False, "Фишки должны быть соседними"

        # Проверка первого хода: должен проходить через центр
        if self.first_move:
            center = (self.BOARD_SIZE // 2, self.BOARD_SIZE // 2)
            if center not in [(r, c) for r, c, _ in self.current_move]:
                return False, "Первый ход должен проходить через центр поля"

        # Проверка: подключение к существующим словам (если не первый ход)
        if not self.first_move:
            connected = False
            for r, c, _ in self.current_move:
                # Проверяем соседей
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.BOARD_SIZE and 0 <= nc < self.BOARD_SIZE:
                        if self.board[nr][nc] is not None:
                            connected = True
                            break
                if connected:
                    break
            if not connected:
                return False, "Новое слово должно соединяться с существующими"

        # Проверка слов: собираем все слова, образованные ходом
        words = self._get_words_from_move()
        for word in words:
            if not self.is_valid_word(word):
                return False, f"Слово '{word}' не найдено в словаре"

        return True, ""

    def _get_words_from_move(self) -> list[str]:
        """Получить все слова, образованные текущим ходом."""
        words = []

        # Временно размещаем фишки для проверки
        temp_board = [row[:] for row in self.board]
        for r, c, letter in self.current_move:
            temp_board[r][c] = letter

        # Проверяем основное слово (по направлению хода)
        if self.current_move:
            first_r, first_c, _ = self.current_move[0]
            # Определяем направление
            if len(set(r for r, _, _ in self.current_move)) == 1:
                # Горизонтальное
                row = first_r
                word = ""
                for c in range(self.BOARD_SIZE):
                    if temp_board[row][c] is not None:
                        word += temp_board[row][c]
                    else:
                        if word:
                            words.append(word)
                            word = ""
                if word:
                    words.append(word)
            else:
                # Вертикальное
                col = first_c
                word = ""
                for r in range(self.BOARD_SIZE):
                    if temp_board[r][col] is not None:
                        word += temp_board[r][col]
                    else:
                        if word:
                            words.append(word)
                            word = ""
                if word:
                    words.append(word)

        # Проверяем перпендикулярные слова
        for r, c, _ in self.current_move:
            # Проверяем перпендикулярное направление
            if len(set(rr for rr, _, _ in self.current_move)) == 1:
                # Ход горизонтальный - проверяем вертикаль
                word = ""
                for rr in range(self.BOARD_SIZE):
                    if temp_board[rr][c] is not None:
                        word += temp_board[rr][c]
                    else:
                        if len(word) > 1:
                            words.append(word)
                        word = ""
                if len(word) > 1:
                    words.append(word)
            else:
                # Ход вертикальный - проверяем горизонталь
                word = ""
                for cc in range(self.BOARD_SIZE):
                    if temp_board[r][cc] is not None:
                        word += temp_board[r][cc]
                    else:
                        if len(word) > 1:
                            words.append(word)
                        word = ""
                if len(word) > 1:
                    words.append(word)

        return [w for w in words if len(w) >= 2]

    def calculate_score(self) -> int:
        """Подсчитать очки за текущий ход."""
        if not self.current_move:
            return 0

        score = 0
        word_multiplier = 1

        # Подсчитываем очки за новые фишки
        for r, c, letter in self.current_move:
            letter_value = self.LETTER_VALUES.get(letter.upper(), 0)
            bonus = self.bonus_cells[r][c]

            if bonus == 1:  # x2 буквы
                letter_value *= 2
            elif bonus == 2:  # x3 буквы
                letter_value *= 3
            elif bonus == 3:  # x2 слова
                word_multiplier *= 2
            elif bonus == 4:  # x3 слова
                word_multiplier *= 3

            score += letter_value

        score *= word_multiplier

        # Бонус за использование всех 7 фишек
        if len(self.current_move) == self.TILES_PER_PLAYER:
            score += self.BONUS_ALL_TILES

        return score

    def make_move(self) -> tuple[bool, str]:
        """Сделать ход. Возвращает (успех, сообщение)."""
        if self.game_over or self.current_player != 1:
            return False, "Не ваш ход"

        # Валидация
        valid, error = self.validate_move()
        if not valid:
            return False, error

        # Подсчет очков
        move_score = self.calculate_score()
        self.player_score += move_score

        # Размещаем фишки на поле
        tiles = self.player_tiles
        for r, c, letter in self.current_move:
            self.board[r][c] = letter
            tiles.remove(letter)

        # Добираем фишки
        while len(tiles) < self.TILES_PER_PLAYER and self.bag:
            tiles.append(self.bag.pop())

        # Первый ход сделан
        if self.first_move:
            self.first_move = False

        # Очищаем ход
        self.current_move = []
        self.passes_count = 0

        # Проверка окончания игры
        if not self.bag and (not self.player_tiles or not self.ai_tiles):
            self._end_game()

        return True, f"Ход принят! +{move_score} очков"

    def _end_game(self) -> None:
        """Завершить игру и подсчитать финальные очки."""
        self.game_over = True

        # Вычитаем оставшиеся фишки
        player_penalty = sum(self.LETTER_VALUES.get(t.upper(), 0) for t in self.player_tiles)
        ai_penalty = sum(self.LETTER_VALUES.get(t.upper(), 0) for t in self.ai_tiles)

        self.player_score -= player_penalty
        self.ai_score -= ai_penalty

        # Если кто-то выложил все фишки - добавляем очки противника
        if not self.player_tiles:
            self.player_score += ai_penalty
        elif not self.ai_tiles:
            self.ai_score += player_penalty

    def get_state(self) -> dict:
        """Получить состояние для фронтенда"""
        return {
            "board": [[cell if cell else "" for cell in row] for row in self.board],
            "bonus_cells": self.bonus_cells,
            "player_tiles": self.player_tiles,
            "ai_tiles": self.ai_tiles,
            "player_score": self.player_score,
            "ai_score": self.ai_score,
            "current_player": self.current_player,
            "game_over": self.game_over,
            "first_move": self.first_move,
            "current_move": self.current_move,
            "bag_count": len(self.bag),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EruditeGame":
        """Восстановить игру из словаря"""
        game = cls.__new__(cls)

        # Восстанавливаем поле
        board_data = data.get("board", [])
        game.board = [[cell if cell else None for cell in row] for row in board_data]
        if not game.board or len(game.board) != cls.BOARD_SIZE:
            game.board = [[None] * cls.BOARD_SIZE for _ in range(cls.BOARD_SIZE)]

        # Бонусные клетки
        game.bonus_cells = data.get(
            "bonus_cells", [[0] * cls.BOARD_SIZE for _ in range(cls.BOARD_SIZE)]
        )
        game.player_tiles = data.get("player_tiles", [])
        game.ai_tiles = data.get("ai_tiles", [])
        game.bag = data.get("bag", [])
        game.player_score = data.get("player_score", 0)
        game.ai_score = data.get("ai_score", 0)
        game.current_player = data.get("current_player", 1)
        game.game_over = data.get("game_over", False)
        game.first_move = data.get("first_move", True)
        game.passes_count = data.get("passes_count", 0)
        game.current_move = data.get("current_move", [])

        from bot.services.erudite_dictionary import is_valid_word

        game.is_valid_word = is_valid_word

        return game
