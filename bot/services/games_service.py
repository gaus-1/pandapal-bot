"""
Сервис игр для PandaPalGo.
Реализует логику игр: крестики-нолики, виселица, 2048.
Включает AI противника (панда) для игры с ребенком.
"""

import random
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from bot.models import GameSession, GameStats
from bot.services.gamification_service import GamificationService


class TicTacToeAI:
    """AI противник для крестиков-ноликов (панда)"""

    def __init__(self, difficulty: str = "medium"):
        """
        Args:
            difficulty: 'easy', 'medium', 'hard'
        """
        self.difficulty = difficulty

    def get_best_move(self, board: List[Optional[str]], player: str) -> int:
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
            # Средний: пытается выиграть, иначе блокирует, иначе случайный
            # 1. Попытка выиграть
            move = self._find_winning_move(board, player)
            if move != -1:
                return move

            # 2. Блокировка противника
            move = self._find_winning_move(board, opponent)
            if move != -1:
                return move

            # 3. Центр если свободен
            if board[4] is None:
                return 4

            # 4. Случайный ход
            available = [i for i in range(9) if board[i] is None]
            return random.choice(available) if available else -1

        else:  # hard
            # Сложный: minimax алгоритм
            _, move = self._minimax(board, player, True)
            return move

    def _find_winning_move(self, board: List[Optional[str]], player: str) -> int:
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
        self, board: List[Optional[str]], player: str, is_maximizing: bool
    ) -> Tuple[int, int]:
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

    def _check_winner(self, board: List[Optional[str]]) -> Optional[str]:
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

    def _is_board_full(self, board: List[Optional[str]]) -> bool:
        """Проверить заполнена ли доска"""
        return all(cell is not None for cell in board)


class HangmanAI:
    """AI для виселицы - выбор слова и подсказок"""

    WORDS_BY_AGE = {
        6: ["кот", "дом", "мама", "папа", "солнце", "вода", "хлеб", "книга"],
        7: ["школа", "учитель", "ученик", "тетрадь", "ручка", "карандаш"],
        8: ["математика", "чтение", "письмо", "рисование", "музыка"],
        9: ["география", "история", "биология", "физика", "химия"],
        10: ["эксперимент", "лаборатория", "исследование", "открытие"],
        11: ["литература", "произведение", "автор", "персонаж"],
        12: ["алгебра", "геометрия", "уравнение", "формула"],
        13: ["философия", "логика", "анализ", "синтез"],
        14: ["программирование", "алгоритм", "структура", "функция"],
        15: ["квантовая", "релятивистская", "теоретическая", "практическая"],
    }

    def get_word(self, age: Optional[int] = None) -> str:
        """Получить слово для игры"""
        if age and age in self.WORDS_BY_AGE:
            words = self.WORDS_BY_AGE[age]
        else:
            # Объединяем все слова
            words = []
            for age_words in self.WORDS_BY_AGE.values():
                words.extend(age_words)

        return random.choice(words).upper()

    def get_hint(self, word: str, guessed_letters: List[str], mistakes: int) -> Optional[str]:
        """
        Получить подсказку для игрока (панда помогает).

        Args:
            word: Загаданное слово
            guessed_letters: Уже угаданные буквы
            mistakes: Количество ошибок

        Returns:
            Optional[str]: Подсказка или None
        """
        if mistakes >= 5:  # Помогаем когда много ошибок
            missing_letters = [c for c in word if c not in guessed_letters]
            if missing_letters:
                # Подсказываем частую букву
                return f"Попробуй букву '{missing_letters[0]}'"

        return None


class GamesService:
    """Сервис для управления играми"""

    def __init__(self, db: Session):  # noqa: D107
        self.db = db
        self.tic_tac_toe_ai = TicTacToeAI(difficulty="medium")
        self.hangman_ai = HangmanAI()

    def create_game_session(
        self, telegram_id: int, game_type: str, initial_state: Optional[Dict] = None
    ) -> GameSession:
        """
        Создать новую игровую сессию.

        Args:
            telegram_id: Telegram ID пользователя
            game_type: Тип игры ('tic_tac_toe', 'hangman', '2048')
            initial_state: Начальное состояние игры

        Returns:
            GameSession: Созданная сессия
        """
        session = GameSession(
            user_telegram_id=telegram_id,
            game_type=game_type,
            game_state=initial_state or {},
            result="in_progress",
        )
        self.db.add(session)
        self.db.flush()
        logger.info(f"🎮 Создана игровая сессия: user={telegram_id}, game={game_type}")
        return session

    def update_game_session(
        self, session_id: int, game_state: Dict, result: Optional[str] = None
    ) -> GameSession:
        """
        Обновить игровую сессию.

        Args:
            session_id: ID сессии
            game_state: Новое состояние игры
            result: Результат ('win', 'loss', 'draw', 'in_progress')

        Returns:
            GameSession: Обновленная сессия
        """
        session = self.db.get(GameSession, session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        if game_state:
            if session.game_state is None:
                session.game_state = {}
            if isinstance(game_state, dict):
                # SQLAlchemy JSON требует явного присваивания нового объекта
                current_state = (
                    dict(session.game_state) if isinstance(session.game_state, dict) else {}
                )
                current_state.update(game_state)
                session.game_state = current_state
            else:
                session.game_state = game_state

        if result:
            session.result = result
            if result != "in_progress":
                session.finished_at = datetime.now(timezone.utc)
                if session.started_at:
                    # Нормализуем timezone для обоих datetime
                    finished = session.finished_at
                    started = session.started_at
                    if finished.tzinfo is None:
                        finished = finished.replace(tzinfo=timezone.utc)
                    if started.tzinfo is None:
                        started = started.replace(tzinfo=timezone.utc)
                    delta = finished - started
                    session.duration_seconds = int(delta.total_seconds())

        self.db.flush()
        return session

    def finish_game_session(
        self, session_id: int, result: str, score: Optional[int] = None
    ) -> GameSession:
        """
        Завершить игровую сессию и обновить статистику.

        Args:
            session_id: ID сессии
            result: Результат ('win', 'loss', 'draw')
            score: Финальный счет (для 2048)

        Returns:
            GameSession: Завершенная сессия
        """
        session = self.update_game_session(session_id, {}, result)
        if score is not None:
            session.score = score

        # Обновляем статистику
        self._update_game_stats(session.user_telegram_id, session.game_type, result, score)

        # Проверяем достижения
        self._check_game_achievements(session.user_telegram_id, session.game_type, result)

        self.db.commit()
        logger.info(f"🎮 Игра завершена: session={session_id}, result={result}, score={score}")
        return session

    def _update_game_stats(
        self, telegram_id: int, game_type: str, result: str, score: Optional[int] = None
    ) -> None:
        """Обновить статистику игры"""
        stmt = select(GameStats).where(
            and_(
                GameStats.user_telegram_id == telegram_id,
                GameStats.game_type == game_type,
            )
        )
        stats = self.db.scalar(stmt)

        if not stats:
            stats = GameStats(
                user_telegram_id=telegram_id,
                game_type=game_type,
                total_games=0,
                wins=0,
                losses=0,
                draws=0,
            )
            self.db.add(stats)

        stats.total_games += 1
        stats.last_played_at = datetime.now(timezone.utc)

        if result == "win":
            stats.wins += 1
        elif result == "loss":
            stats.losses += 1
        elif result == "draw":
            stats.draws += 1

        if score is not None:
            if stats.total_score is None:
                stats.total_score = 0
            stats.total_score += score
            if stats.best_score is None or score > stats.best_score:
                stats.best_score = score

        self.db.flush()

    def _check_game_achievements(self, telegram_id: int, game_type: str, result: str) -> None:
        """Проверить и разблокировать игровые достижения"""
        gamification_service = GamificationService(self.db)

        # Получаем статистику игры (возвращает dict)
        stats = self.get_game_stats(telegram_id, game_type)

        # Проверяем достижения
        if result == "win":
            wins = stats.get("wins", 0)
            # "Победил панду 1 раз"
            if wins == 1:
                gamification_service.check_and_unlock_achievements(telegram_id)

            # "Победил панду 10 раз"
            if wins == 10:
                gamification_service.check_and_unlock_achievements(telegram_id)

            # "Победил панду 50 раз"
            if wins == 50:
                gamification_service.check_and_unlock_achievements(telegram_id)

        # "Сыграл 100 партий"
        total_games = stats.get("total_games", 0)
        if total_games == 100:
            gamification_service.check_and_unlock_achievements(telegram_id)

    def get_game_stats(self, telegram_id: int, game_type: Optional[str] = None) -> Dict:
        """
        Получить статистику игр пользователя.

        Args:
            telegram_id: Telegram ID пользователя
            game_type: Тип игры (опционально)

        Returns:
            Dict: Статистика игры или всех игр
        """
        if game_type:
            stmt = select(GameStats).where(
                and_(
                    GameStats.user_telegram_id == telegram_id,
                    GameStats.game_type == game_type,
                )
            )
            stats = self.db.scalar(stmt)
            if stats:
                return stats.to_dict()
            return {
                "game_type": game_type,
                "total_games": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "win_rate": 0.0,
                "best_score": None,
                "total_score": 0,
                "last_played_at": None,
            }

        # Все игры
        stmt = select(GameStats).where(GameStats.user_telegram_id == telegram_id)
        all_stats = self.db.scalars(stmt).all()

        result = {}
        for stats in all_stats:
            result[stats.game_type] = stats.to_dict()

        return result

    def get_recent_sessions(
        self, telegram_id: int, game_type: Optional[str] = None, limit: int = 10
    ) -> List[GameSession]:
        """
        Получить последние игровые сессии.

        Args:
            telegram_id: Telegram ID пользователя
            game_type: Тип игры (опционально)
            limit: Количество сессий

        Returns:
            List[GameSession]: Список сессий
        """
        stmt = (
            select(GameSession)
            .where(GameSession.user_telegram_id == telegram_id)
            .order_by(GameSession.started_at.desc())
            .limit(limit)
        )

        if game_type:
            stmt = stmt.where(GameSession.game_type == game_type)

        return list(self.db.scalars(stmt).all())

    # ============ ЛОГИКА ИГР ============

    def tic_tac_toe_make_move(self, session_id: int, position: int, user_symbol: str = "X") -> Dict:
        """
        Сделать ход в крестики-нолики.

        Args:
            session_id: ID сессии
            position: Позиция (0-8)
            user_symbol: Символ пользователя ('X')

        Returns:
            Dict: Обновленное состояние игры
        """
        session = self.db.get(GameSession, session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        # Получаем текущее состояние доски
        if session.game_state and isinstance(session.game_state, dict):
            board = session.game_state.get("board", [None] * 9)
        else:
            board = [None] * 9

        # Проверяем валидность позиции
        if position < 0 or position >= 9:
            raise ValueError(f"Invalid position: {position}. Must be between 0 and 8")

        if board[position] is not None:
            raise ValueError("Position already taken")

        # Ход пользователя
        board[position] = user_symbol
        ai_symbol = "O"

        # Проверяем победу пользователя
        winner = self._check_tic_tac_toe_winner(board)
        if winner == user_symbol:
            self.finish_game_session(session_id, "win")
            return {
                "board": board,
                "winner": "user",
                "game_over": True,
                "ai_move": None,
            }

        # Проверяем ничью (все клетки заняты)
        if all(cell is not None for cell in board):
            self.finish_game_session(session_id, "draw")
            self.db.commit()
            return {
                "board": board,
                "winner": None,
                "game_over": True,
                "ai_move": None,
            }

        # Ход AI (панда) - только если игра не закончилась
        ai_position = self.tic_tac_toe_ai.get_best_move(board, ai_symbol)
        if ai_position != -1 and ai_position < len(board) and board[ai_position] is None:
            board[ai_position] = ai_symbol

            # Проверяем победу AI после его хода
            winner = self._check_tic_tac_toe_winner(board)
            if winner == ai_symbol:
                self.finish_game_session(session_id, "loss")
                self.db.commit()
                return {
                    "board": board,
                    "winner": "ai",
                    "game_over": True,
                    "ai_move": ai_position,
                }

            # Проверяем ничью после хода AI
            if all(cell is not None for cell in board):
                self.finish_game_session(session_id, "draw")
                self.db.commit()
                return {
                    "board": board,
                    "winner": None,
                    "game_over": True,
                    "ai_move": ai_position,
                }

        # Обновляем состояние игры в БД
        self.update_game_session(session_id, {"board": board}, "in_progress")
        self.db.commit()

        return {
            "board": board,
            "winner": None,
            "game_over": False,
            "ai_move": ai_position if ai_position != -1 else None,
        }

    def _check_tic_tac_toe_winner(self, board: List[Optional[str]]) -> Optional[str]:
        """Проверить победителя в крестиках-ноликах"""
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

    def hangman_guess_letter(self, session_id: int, letter: str) -> Dict:
        """
        Угадать букву в виселице.

        Args:
            session_id: ID сессии
            letter: Буква (одна)

        Returns:
            Dict: Обновленное состояние игры
        """
        session = self.db.get(GameSession, session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        state = session.game_state
        word = state.get("word", "")
        guessed_letters = state.get("guessed_letters", [])
        mistakes = state.get("mistakes", 0)

        # Приводим букву к верхнему регистру для регистронезависимого сравнения
        letter = letter.upper()
        # Убеждаемся, что слово тоже в верхнем регистре
        word = word.upper()

        # Проверяем, что это одна буква алфавита
        if not letter.isalpha() or len(letter) != 1:
            raise ValueError("Letter must be a single alphabetic character")

        # Обработка повторных букв: не засчитываем как ошибку, но и не приносим пользы
        if letter in guessed_letters:
            raise ValueError("Letter already guessed")

        guessed_letters.append(letter)

        # Обновляем слово в состоянии (в верхнем регистре)
        state["word"] = word

        # Проверяем наличие буквы в слове (регистронезависимо)
        if letter in word:
            # Правильная буква - обновляем состояние
            state["guessed_letters"] = guessed_letters
        else:
            # Неправильная буква - увеличиваем счетчик ошибок
            mistakes += 1
            state["mistakes"] = mistakes
            state["guessed_letters"] = guessed_letters

        # Проверяем победу: все уникальные буквы слова угаданы
        # Игнорируем пробелы и другие не-буквенные символы
        unique_letters_in_word = set(c for c in word if c.isalpha())
        if unique_letters_in_word.issubset(set(guessed_letters)):
            self.finish_game_session(session_id, "win")
            return {
                "word": word,
                "guessed_letters": guessed_letters,
                "mistakes": mistakes,
                "game_over": True,
                "won": True,
            }

        # Проверяем поражение
        if mistakes >= 6:
            self.finish_game_session(session_id, "loss")
            return {
                "word": word,
                "guessed_letters": guessed_letters,
                "mistakes": mistakes,
                "game_over": True,
                "won": False,
            }

        # Обновляем состояние
        self.update_game_session(session_id, state, "in_progress")
        self.db.commit()

        return {
            "word": word,
            "guessed_letters": guessed_letters,
            "mistakes": mistakes,
            "game_over": False,
            "won": None,
        }

    def game_2048_move(self, session_id: int, direction: str) -> Dict:
        """
        Сделать ход в 2048.

        Args:
            session_id: ID сессии
            direction: Направление ('up', 'down', 'left', 'right')

        Returns:
            Dict: Обновленное состояние игры
        """
        session = self.db.get(GameSession, session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        board = session.game_state.get("board", self._init_2048_board())

        # Делаем ход
        new_board, new_score = self._move_2048(board, direction)

        # Добавляем новую клетку только если доска изменилась
        board_changed = new_board != board
        if board_changed:
            new_board = self._add_random_tile(new_board)

        # Проверяем поражение
        if self._is_2048_game_over(new_board):
            self.finish_game_session(session_id, "loss", new_score)
            self.db.commit()
            return {
                "board": new_board,
                "score": new_score,
                "game_over": True,
                "won": False,
            }

        # Проверяем победу (2048)
        if any(any(cell == 2048 for cell in row) for row in new_board):
            if session.game_state.get("won") is None:
                session.game_state["won"] = True

        # Обновляем состояние
        self.update_game_session(
            session_id, {"board": new_board, "score": new_score}, "in_progress"
        )

        return {
            "board": new_board,
            "score": new_score,
            "game_over": False,
            "won": session.game_state.get("won", False),
        }

    def _init_2048_board(self) -> List[List[int]]:
        """Инициализировать доску 2048"""
        board = [[0] * 4 for _ in range(4)]
        board = self._add_random_tile(board)
        board = self._add_random_tile(board)
        return board

    def _add_random_tile(self, board: List[List[int]]) -> List[List[int]]:
        """
        Добавить случайную клетку (2 или 4).
        Вероятность: 90% для 2, 10% для 4 (как в оригинальной игре 2048).
        """
        empty = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
        if empty:
            i, j = random.choice(empty)
            # Большая вероятность выпадения двойки (90%)
            board[i][j] = 2 if random.random() < 0.9 else 4
        return board

    def _move_2048(self, board: List[List[int]], direction: str) -> Tuple[List[List[int]], int]:
        """Сделать ход в 2048"""
        new_board = [row[:] for row in board]
        score = 0

        if direction == "left":
            for i in range(4):
                new_board[i], row_score = self._merge_row_left(new_board[i])
                score += row_score
        elif direction == "right":
            for i in range(4):
                new_board[i], row_score = self._merge_row_right(new_board[i])
                score += row_score
        elif direction == "up":
            for j in range(4):
                col = [new_board[i][j] for i in range(4)]
                merged_col, col_score = self._merge_row_left(col)
                score += col_score
                for i in range(4):
                    new_board[i][j] = merged_col[i]
        elif direction == "down":
            for j in range(4):
                col = [new_board[i][j] for i in range(4)]
                merged_col, col_score = self._merge_row_right(col)
                score += col_score
                for i in range(4):
                    new_board[i][j] = merged_col[i]

        return new_board, score

    def _merge_row_left(self, row: List[int]) -> Tuple[List[int], int]:
        """Объединить строку влево"""
        # Убираем нули
        row = [x for x in row if x != 0]
        score = 0

        # Объединяем одинаковые
        merged = []
        i = 0
        while i < len(row):
            if i < len(row) - 1 and row[i] == row[i + 1]:
                merged.append(row[i] * 2)
                score += row[i] * 2
                i += 2
            else:
                merged.append(row[i])
                i += 1

        # Дополняем нулями
        merged.extend([0] * (4 - len(merged)))
        return merged, score

    def _merge_row_right(self, row: List[int]) -> Tuple[List[int], int]:
        """Объединить строку вправо"""
        merged, score = self._merge_row_left(row[::-1])
        return merged[::-1], score

    def _is_2048_game_over(self, board: List[List[int]]) -> bool:
        """Проверить окончание игры 2048"""
        # Есть пустые клетки
        if any(any(cell == 0 for cell in row) for row in board):
            return False

        # Проверяем возможные ходы
        for i in range(4):
            for j in range(4):
                if (i < 3 and board[i][j] == board[i + 1][j]) or (
                    j < 3 and board[i][j] == board[i][j + 1]
                ):
                    return False

        return True
