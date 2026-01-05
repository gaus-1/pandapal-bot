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


class CheckersAI:
    """AI для шашек (панда)"""

    def get_best_move(
        self, board: List[List[Optional[str]]], player: str
    ) -> Optional[Tuple[int, int, int, int]]:
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
        capture_moves = [m for m in moves if self._is_capture_move(board, m, player)]
        if capture_moves:
            return random.choice(capture_moves)

        forward_moves = [m for m in moves if self._is_forward_move(m, player)]
        if forward_moves:
            return random.choice(forward_moves)

        return random.choice(moves)

    def _get_all_moves(
        self, board: List[List[Optional[str]]], player: str
    ) -> List[Tuple[int, int, int, int]]:
        """Получить все возможные ходы для игрока"""
        moves = []
        for row in range(8):
            for col in range(8):
                if board[row][col] == player:
                    # Проверяем возможные ходы из этой позиции
                    # AI двигается вниз (увеличение row, так как он вверху доски)
                    for dr, dc in [(1, -1), (1, 1)]:
                        new_row, new_col = row + dr, col + dc
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if board[new_row][new_col] is None:
                                moves.append((row, col, new_row, new_col))
                            elif board[new_row][new_col] == "user":
                                # Проверяем возможность взятия
                                jump_row, jump_col = new_row + dr, new_col + dc
                                if 0 <= jump_row < 8 and 0 <= jump_col < 8:
                                    if board[jump_row][jump_col] is None:
                                        moves.append((row, col, jump_row, jump_col))
        return moves

    def _is_capture_move(
        self, board: List[List[Optional[str]]], move: Tuple[int, int, int, int], player: str
    ) -> bool:
        """Проверить, является ли ход взятием фишки"""
        from_row, from_col, to_row, to_col = move
        # Если ход на 2 клетки по диагонали - это взятие
        return abs(to_row - from_row) == 2 and abs(to_col - from_col) == 2

    def _is_forward_move(self, move: Tuple[int, int, int, int], player: str) -> bool:
        """Проверить, является ли ход движением вперед"""
        from_row, _, to_row, _ = move
        # Для AI (который вверху) движение вперед = движение вниз (увеличение row)
        return to_row > from_row


class GamesService:
    """Сервис для управления играми"""

    def __init__(self, db: Session):  # noqa: D107
        self.db = db
        self.tic_tac_toe_ai = TicTacToeAI(difficulty="medium")
        self.checkers_ai = CheckersAI()

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

        # Проверяем победу пользователя после его хода
        winner = self._check_tic_tac_toe_winner(board)
        if winner == user_symbol:
            self.finish_game_session(session_id, "win")
            return {
                "board": board,
                "winner": "user",
                "game_over": True,
                "ai_move": None,
            }

        # Ход AI (панда) - только если игра не закончилась
        ai_position = self.tic_tac_toe_ai.get_best_move(board, ai_symbol)

        # Проверяем, что AI может сделать ход
        if ai_position == -1 or ai_position >= len(board) or board[ai_position] is not None:
            # Если доска заполнена, это ничья
            if all(cell is not None for cell in board):
                self.finish_game_session(session_id, "draw")
                self.db.commit()
                return {
                    "board": board,
                    "winner": None,
                    "game_over": True,
                    "ai_move": None,
                }
            # Если есть свободные клетки, но AI не может сделать ход - это ошибка AI
            # В этом случае просто продолжаем игру без хода AI
            logger.warning(f"AI cannot make a move but board is not full. Board: {board}")
            self.update_game_session(session_id, {"board": board}, "in_progress")
            self.db.commit()
            return {
                "board": board,
                "winner": None,
                "game_over": False,
                "ai_move": None,
            }

        # Делаем ход AI
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

        # Проверяем ничью после хода AI (все клетки заполнены)
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

    def checkers_move(
        self, session_id: int, from_row: int, from_col: int, to_row: int, to_col: int
    ) -> Dict:
        """
        Сделать ход в шашках.

        Args:
            session_id: ID сессии
            from_row: Начальная строка (0-7)
            from_col: Начальный столбец (0-7)
            to_row: Конечная строка (0-7)
            to_col: Конечный столбец (0-7)

        Returns:
            Dict: Обновленное состояние игры
        """
        session = self.db.get(GameSession, session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        # Получаем текущее состояние доски
        if session.game_state and isinstance(session.game_state, dict):
            board = session.game_state.get("board", self._init_checkers_board())
        else:
            board = self._init_checkers_board()

        # Проверяем валидность хода
        if not self._is_valid_move(board, from_row, from_col, to_row, to_col, "user"):
            raise ValueError("Invalid move")

        # Делаем ход пользователя
        board = self._make_move(board, from_row, from_col, to_row, to_col, "user")

        # Проверяем победу пользователя
        if self._check_checkers_winner(board) == "user":
            self.finish_game_session(session_id, "win")
            return {
                "board": board,
                "winner": "user",
                "game_over": True,
                "ai_move": None,
            }

        # Ход AI (панда)
        ai_move = self.checkers_ai.get_best_move(board, "ai")
        if ai_move:
            ai_from_row, ai_from_col, ai_to_row, ai_to_col = ai_move
            board = self._make_move(board, ai_from_row, ai_from_col, ai_to_row, ai_to_col, "ai")

            # Проверяем победу AI
            if self._check_checkers_winner(board) == "ai":
                self.finish_game_session(session_id, "loss")
                return {
                    "board": board,
                    "winner": "ai",
                    "game_over": True,
                    "ai_move": ai_move,
                }

        # Обновляем состояние игры в БД
        self.update_game_session(session_id, {"board": board}, "in_progress")
        self.db.commit()

        return {
            "board": board,
            "winner": None,
            "game_over": False,
            "ai_move": ai_move if ai_move else None,
        }

    def _init_checkers_board(self) -> List[List[Optional[str]]]:
        """Инициализировать доску шашек 8x8"""
        board = [[None] * 8 for _ in range(8)]
        # Пользователь (внизу визуально) - последние 3 ряда
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    board[row][col] = "user"
        # AI (вверху визуально) - первые 3 ряда
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:
                    board[row][col] = "ai"
        return board

    def _is_valid_move(
        self,
        board: List[List[Optional[str]]],
        from_row: int,
        from_col: int,
        to_row: int,
        to_col: int,
        player: str,
    ) -> bool:
        """Проверить валидность хода"""
        # Проверяем границы
        if not (0 <= from_row < 8 and 0 <= from_col < 8):
            return False
        if not (0 <= to_row < 8 and 0 <= to_col < 8):
            return False

        # Проверяем, что на начальной позиции есть фишка игрока
        if board[from_row][from_col] != player:
            return False

        # Проверяем, что конечная позиция свободна
        if board[to_row][to_col] is not None:
            return False

        # Проверяем, что ход по диагонали
        row_diff = to_row - from_row
        col_diff = to_col - from_col
        if abs(row_diff) != abs(col_diff):
            return False

        # Пользователь двигается вверх (уменьшение row, так как он внизу доски)
        if player == "user":
            if row_diff >= 0:
                return False
            # Обычный ход - на 1 клетку
            if abs(row_diff) == 1:
                return True
            # Взятие - на 2 клетки
            if abs(row_diff) == 2:
                mid_row, mid_col = from_row + row_diff // 2, from_col + col_diff // 2
                return board[mid_row][mid_col] == "ai"

        return False

    def _make_move(
        self,
        board: List[List[Optional[str]]],
        from_row: int,
        from_col: int,
        to_row: int,
        to_col: int,
        player: str,
    ) -> List[List[Optional[str]]]:
        """Сделать ход на доске"""
        new_board = [row[:] for row in board]
        new_board[to_row][to_col] = new_board[from_row][from_col]
        new_board[from_row][from_col] = None

        # Если это взятие, удаляем фишку противника
        row_diff = to_row - from_row
        col_diff = to_col - from_col
        if abs(row_diff) == 2:
            mid_row, mid_col = from_row + row_diff // 2, from_col + col_diff // 2
            new_board[mid_row][mid_col] = None

        return new_board

    def _check_checkers_winner(self, board: List[List[Optional[str]]]) -> Optional[str]:
        """Проверить победителя в шашках"""
        user_count = sum(1 for row in board for cell in row if cell == "user")
        ai_count = sum(1 for row in board for cell in row if cell == "ai")

        if user_count == 0:
            return "ai"
        if ai_count == 0:
            return "user"

        # Проверяем, есть ли у игрока возможные ходы
        user_has_moves = self._has_valid_moves(board, "user")
        ai_has_moves = self._has_valid_moves(board, "ai")

        if not user_has_moves:
            return "ai"
        if not ai_has_moves:
            return "user"

        return None

    def _has_valid_moves(self, board: List[List[Optional[str]]], player: str) -> bool:
        """Проверить, есть ли у игрока возможные ходы"""
        for row in range(8):
            for col in range(8):
                if board[row][col] == player:
                    # Проверяем все возможные ходы из этой позиции
                    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                        new_row, new_col = row + dr, col + dc
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if self._is_valid_move(board, row, col, new_row, new_col, player):
                                return True
        return False

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
