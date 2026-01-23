"""
Логика игры Эрудит (Scrabble).
"""

import random


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
                    if (
                        0 <= nr < self.BOARD_SIZE
                        and 0 <= nc < self.BOARD_SIZE
                        and self.board[nr][nc] is not None
                    ):
                        connected = True
                        break
                if connected:
                    break
            if not connected:
                return False, "Новое слово должно соединяться с существующими"

            # Проверяем что образуется хотя бы одно валидное слово длиной > 1
            words = self._get_words_from_move()
            if not words:
                return False, "Ход не образует валидных слов"

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
            if len({r for r, _, _ in self.current_move}) == 1:
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
            if len({rr for rr, _, _ in self.current_move}) == 1:
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

        # Убираем дубликаты и слова короче 2 букв
        return list({w for w in words if len(w) >= 2})

    def calculate_score(self) -> int:
        """Подсчитать очки за текущий ход."""
        if not self.current_move:
            return 0

        # Временно размещаем фишки для расчета
        temp_board = [row[:] for row in self.board]
        for r, c, letter in self.current_move:
            temp_board[r][c] = letter

        total_score = 0

        # Получаем все слова образованные ходом
        words_list = self._get_words_from_move()

        # Подсчитываем очки за каждое слово
        for word in words_list:
            word_score = 0
            word_multiplier = 1

            # Находим позиции букв этого слова
            # Определяем направление основного хода
            if len({r for r, _, _ in self.current_move}) == 1:
                # Горизонтальный ход - ищем слово горизонтально
                row = self.current_move[0][0]
                for c in range(self.BOARD_SIZE):
                    if temp_board[row][c] and temp_board[row][c] in word:
                        letter = temp_board[row][c]
                        letter_value = self.LETTER_VALUES.get(letter.upper(), 0)

                        # Применяем бонусы только для новых фишек
                        is_new = any(r == row and c == col for r, col, _ in self.current_move)
                        if is_new:
                            bonus = self.bonus_cells[row][c]
                            if bonus == 1:  # x2 буквы
                                letter_value *= 2
                            elif bonus == 2:  # x3 буквы
                                letter_value *= 3
                            elif bonus == 3:  # x2 слова
                                word_multiplier *= 2
                            elif bonus == 4:  # x3 слова
                                word_multiplier *= 3

                        word_score += letter_value
            else:
                # Вертикальный ход - ищем слово вертикально
                col = self.current_move[0][1]
                for r in range(self.BOARD_SIZE):
                    if temp_board[r][col] and temp_board[r][col] in word:
                        letter = temp_board[r][col]
                        letter_value = self.LETTER_VALUES.get(letter.upper(), 0)

                        # Применяем бонусы только для новых фишек
                        is_new = any(r == row and col == c for row, c, _ in self.current_move)
                        if is_new:
                            bonus = self.bonus_cells[r][col]
                            if bonus == 1:  # x2 буквы
                                letter_value *= 2
                            elif bonus == 2:  # x3 буквы
                                letter_value *= 3
                            elif bonus == 3:  # x2 слова
                                word_multiplier *= 2
                            elif bonus == 4:  # x3 слова
                                word_multiplier *= 3

                        word_score += letter_value

            total_score += word_score * word_multiplier

        # Бонус за использование всех 7 фишек
        if len(self.current_move) == self.TILES_PER_PLAYER:
            total_score += self.BONUS_ALL_TILES

        return total_score

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

        # Переключаем игрока на AI
        self.current_player = 2

        # Проверка окончания игры
        if not self.bag and (not self.player_tiles or not self.ai_tiles):
            self._end_game()

        return True, f"Ход принят! +{move_score} очков"

    def make_ai_move(self) -> tuple[bool, str]:
        """
        Сделать ход AI (простая логика для начала).
        Пытается выложить любое валидное слово из своих фишек.
        """
        if self.game_over or self.current_player != 2:
            return False, "Не ход AI"

        # Простая стратегия: попробовать выложить любое валидное слово
        # Для начала просто пропускаем ход (заглушка)
        # TODO: Реализовать полноценный AI

        # Пропускаем ход
        self.passes_count += 1
        self.current_player = 1  # Переключаем обратно на игрока

        # Проверка окончания (2 пропуска подряд)
        if self.passes_count >= 2:
            self._end_game()
            return True, "AI пропустил ход. Игра окончена."

        return True, "AI пропустил ход"

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
