"""
Сервис игр для PandaPalGo.
Реализует логику игр: крестики-нолики, виселица, 2048.
Включает AI противника (панда) для игры с ребенком.
"""

import asyncio
import random
from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from bot.models import GameSession, GameStats
from bot.services.game_engines import CheckersGame, EruditeGame, Game2048, TicTacToe
from bot.services.gamification_service import GamificationService


def _debug_log(
    *,
    hypothesis_id: str,  # noqa: ARG001
    location: str,  # noqa: ARG001
    message: str,  # noqa: ARG001
    data: dict | None = None,  # noqa: ARG001
    run_id: str = "initial",  # noqa: ARG001
) -> None:
    """Записать отладочное сообщение в NDJSON-файл debug.log."""
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
        """Получить все возможные ходы для игрока"""
        moves = []
        for row in range(8):
            for col in range(8):
                if board[row][col] == player:
                    moves.extend(self._get_moves_from_position(board, row, col))
        return moves

    def _get_moves_from_position(
        self, board: list[list[str | None]], row: int, col: int
    ) -> list[tuple[int, int, int, int]]:
        """Получить все возможные ходы из заданной позиции."""
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


class GamesService:
    """Сервис для управления играми"""

    def __init__(self, db: Session):  # noqa: D107
        self.db = db
        self.tic_tac_toe_ai = TicTacToeAI(difficulty="medium")
        self.checkers_ai = CheckersAI()

    def create_game_session(
        self, telegram_id: int, game_type: str, initial_state: dict | None = None
    ) -> GameSession:
        """
        Создать новую игровую сессию.

        Args:
            telegram_id: Telegram ID пользователя
            game_type: Тип игры ('tic_tac_toe', 'checkers', '2048')
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
        self, session_id: int, game_state: dict, result: str | None = None
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
                session.finished_at = datetime.now(UTC)
                if session.started_at:
                    # Нормализуем timezone для обоих datetime
                    finished = session.finished_at
                    started = session.started_at
                    if finished.tzinfo is None:
                        finished = finished.replace(tzinfo=UTC)
                    if started.tzinfo is None:
                        started = started.replace(tzinfo=UTC)
                    delta = finished - started
                    session.duration_seconds = int(delta.total_seconds())

        self.db.flush()
        return session

    def finish_game_session(
        self, session_id: int, result: str, score: int | None = None
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
        self, telegram_id: int, game_type: str, result: str, score: int | None = None
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
        stats.last_played_at = datetime.now(UTC)

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

        # Проверяем достижения - вызываем один раз, проверка внутри предотвратит повторные разблокировки
        if result == "win":
            wins = stats.get("wins", 0)
            # Проверяем все достижения за победы одним вызовом
            if wins >= 1:  # Если есть хотя бы 1 победа, проверяем все достижения
                gamification_service.check_and_unlock_achievements(telegram_id)

        # "Сыграл 100 партий" - отдельная проверка
        total_games = stats.get("total_games", 0)
        if total_games >= 100:
            gamification_service.check_and_unlock_achievements(telegram_id)

    def get_game_stats(self, telegram_id: int, game_type: str | None = None) -> dict:
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
        self, telegram_id: int, game_type: str | None = None, limit: int = 10
    ) -> list[GameSession]:
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

    # ЛОГИКА ИГР

    async def tic_tac_toe_make_move(self, session_id: int, position: int) -> dict:
        """
        Сделать ход в крестики-нолики.

        Args:
            session_id: ID сессии
            position: Позиция (0-8)

        Returns:
            Dict: Обновленное состояние игры
        """
        session = self.db.get(GameSession, session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        # Восстанавливаем или создаем игру
        if session.game_state and isinstance(session.game_state, dict):
            game_state = session.game_state
            saved_board = game_state.get("board", [None] * 9)
            # Восстанавливаем игру из сохраненного состояния
            game = TicTacToe()
            # Восстанавливаем доску из сохраненного состояния
            for i, cell in enumerate(saved_board):
                if i < 9:  # Проверяем границы
                    row, col = i // 3, i % 3
                    if cell == "X":
                        game.board[row][col] = 1
                        game.moves_count += 1
                    elif cell == "O":
                        game.board[row][col] = 2
                        game.moves_count += 1
            # Определяем текущего игрока по количеству ходов
            game.current_player = 1 if game.moves_count % 2 == 0 else 2
            # Проверяем, не закончена ли уже игра
            if game_state.get("winner"):
                game.winner = 1 if game_state.get("winner") == "user" else 2
            if game_state.get("is_draw"):
                game.is_draw = True
        else:
            game = TicTacToe()

        # Конвертируем position (0-8) в row, col
        row, col = position // 3, position % 3

        # Проверяем валидность позиции
        if position < 0 or position >= 9:
            raise ValueError(f"Invalid position: {position}. Must be between 0 and 8")

        if game.board[row][col] is not None:
            raise ValueError("Position already taken")

        # Ход пользователя (1 = X)
        if not game.make_move(row, col):
            raise ValueError("Invalid move")

        # Проверяем победу пользователя
        if game.winner == 1:
            state = game.get_state()
            self.finish_game_session(session_id, "win")
            return {
                "board": state["board"],
                "winner": "user",
                "game_over": True,
                "ai_move": None,
            }

        # Проверяем ничью
        if game.is_draw:
            state = game.get_state()
            self.finish_game_session(session_id, "draw")
            self.db.commit()
            return {
                "board": state["board"],
                "winner": None,
                "game_over": True,
                "ai_move": None,
            }

        # Ход AI (2 = O)
        # Панда думает перед ходом
        await asyncio.sleep(1.5)
        # Находим лучший ход через AI
        frontend_board = game.get_state()["board"]
        ai_position = self.tic_tac_toe_ai.get_best_move(frontend_board, "O")
        if ai_position == -1 or ai_position >= 9:
            # Нет доступных ходов - ничья
            state = game.get_state()
            self.finish_game_session(session_id, "draw")
            self.db.commit()
            return {
                "board": state["board"],
                "winner": None,
                "game_over": True,
                "ai_move": None,
            }

        ai_row, ai_col = ai_position // 3, ai_position % 3
        if not game.make_move(ai_row, ai_col):
            # AI не может сделать ход - ничья
            state = game.get_state()
            self.finish_game_session(session_id, "draw")
            self.db.commit()
            return {
                "board": state["board"],
                "winner": None,
                "game_over": True,
                "ai_move": None,
            }

        # Проверяем победу AI
        if game.winner == 2:
            state = game.get_state()
            self.finish_game_session(session_id, "loss")
            self.db.commit()
            return {
                "board": state["board"],
                "winner": "ai",
                "game_over": True,
                "ai_move": ai_position,
            }

        # Проверяем ничью после хода AI
        if game.is_draw:
            state = game.get_state()
            self.finish_game_session(session_id, "draw")
            self.db.commit()
            return {
                "board": state["board"],
                "winner": None,
                "game_over": True,
                "ai_move": ai_position,
            }

        # Сохраняем состояние
        state = game.get_state()
        self.update_game_session(session_id, {"board": state["board"]}, "in_progress")
        self.db.commit()

        return {
            "board": state["board"],
            "winner": None,
            "game_over": False,
            "ai_move": ai_position,
        }

    def get_checkers_valid_moves(self, session_id: int) -> list[dict]:
        """
        Получить валидные ходы для пользователя в шашках.

        Args:
            session_id: ID сессии

        Returns:
            List[Dict]: Список валидных ходов в формате [{"from": (row, col), "to": (row, col), "capture": (row, col) | None}, ...]
        """
        session = self.db.get(GameSession, session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        # Восстанавливаем или создаем игру
        if session.game_state and isinstance(session.game_state, dict):
            game_state = session.game_state
            board_data = game_state.get("board")
            if board_data and isinstance(board_data, list) and len(board_data) == 8:
                # Восстанавливаем игру из сохраненного состояния
                game = CheckersGame()
                kings_data = game_state.get("kings", [])
                # Конвертируем frontend формат ('user', 'ai', None) в engine формат (1, 2, 0, 3, 4)
                for r in range(8):
                    for c in range(8):
                        cell = (
                            board_data[r][c]
                            if r < len(board_data) and c < len(board_data[r])
                            else None
                        )
                        is_king = (
                            kings_data[r][c]
                            if r < len(kings_data) and c < len(kings_data[r])
                            else False
                        )
                        if cell == "user":
                            game.board[r][c] = 3 if is_king else 1
                        elif cell == "ai":
                            game.board[r][c] = 4 if is_king else 2
                        else:
                            game.board[r][c] = 0
                # Восстанавливаем текущего игрока и другие состояния
                game.current_player = game_state.get("current_player", 1)
                must_capture = game_state.get("must_capture")
                if must_capture and isinstance(must_capture, list) and len(must_capture) == 2:
                    game.must_capture_from = tuple(must_capture)
            else:
                game = CheckersGame()
        else:
            game = CheckersGame()

        # КРИТИЧНО: Проверяем, что очередь пользователя
        # Если current_player != 1, значит очередь AI - пользователь не может ходить
        if game.current_player != 1:
            logger.warning(
                f"⚠️ Попытка получить ходы для пользователя, но очередь AI (current_player={game.current_player})"
            )
            return []

        # Получаем валидные ходы для пользователя (player = 1)
        valid_moves = game.get_valid_moves(1)

        _debug_log(
            hypothesis_id="H1",
            location="GamesService.get_checkers_valid_moves",
            message="Calculated valid moves for user",
            data={
                "session_id": session_id,
                "current_player": game.current_player,
                "must_capture_from": game.must_capture_from,
                "valid_moves_count": len(valid_moves),
            },
        )
        return valid_moves

    async def checkers_move(
        self, session_id: int, from_row: int, from_col: int, to_row: int, to_col: int
    ) -> dict:
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

        # Восстанавливаем или создаем игру
        if session.game_state and isinstance(session.game_state, dict):
            game_state = session.game_state
            board_data = game_state.get("board")
            if board_data and isinstance(board_data, list) and len(board_data) == 8:
                # Восстанавливаем игру из сохраненного состояния
                game = CheckersGame()
                kings_data = game_state.get("kings", [])
                # Конвертируем frontend формат ('user', 'ai', None) в engine формат (1, 2, 0, 3, 4)
                for r in range(8):
                    for c in range(8):
                        cell = (
                            board_data[r][c]
                            if r < len(board_data) and c < len(board_data[r])
                            else None
                        )
                        is_king = (
                            kings_data[r][c]
                            if r < len(kings_data) and c < len(kings_data[r])
                            else False
                        )
                        if cell == "user":
                            game.board[r][c] = 3 if is_king else 1
                        elif cell == "ai":
                            game.board[r][c] = 4 if is_king else 2
                        else:
                            game.board[r][c] = 0
                # Восстанавливаем текущего игрока и другие состояния
                game.current_player = game_state.get("current_player", 1)
                must_capture = game_state.get("must_capture")
                if must_capture and isinstance(must_capture, list) and len(must_capture) == 2:
                    game.must_capture_from = tuple(must_capture)
            else:
                game = CheckersGame()
        else:
            game = CheckersGame()

        # КРИТИЧНО: Проверяем, что очередь пользователя
        # Если current_player != 1, значит очередь AI - пользователь не может ходить
        if game.current_player != 1:
            logger.warning(
                f"⚠️ Попытка хода пользователя, но очередь AI (current_player={game.current_player})"
            )
            raise ValueError("Не ваша очередь ходить")

        # Ход пользователя (player = 1)
        # Получаем валидные ходы для диагностики
        user_valid_moves = game.get_valid_moves(1)

        _debug_log(
            hypothesis_id="H1",
            location="GamesService.checkers_move.before_user",
            message="Before user move",
            data={
                "session_id": session_id,
                "from": [from_row, from_col],
                "to": [to_row, to_col],
                "current_player": game.current_player,
                "must_capture_from": game.must_capture_from,
                "user_valid_moves_count": len(user_valid_moves),
            },
        )
        if not game.make_move(from_row, from_col, to_row, to_col):
            # Логируем детали для отладки
            logger.warning(
                f"⚠️ Невалидный ход пользователя: ({from_row}, {from_col}) -> ({to_row}, {to_col})"
            )
            logger.warning(
                f"📊 Текущий игрок: {game.current_player}, обязательное взятие: {game.must_capture_from}"
            )
            logger.warning(f"📋 Валидных ходов для пользователя: {len(user_valid_moves)}")
            if user_valid_moves:
                logger.warning(f"📋 Примеры валидных ходов: {user_valid_moves[:3]}")
            raise ValueError("Invalid move")

        _debug_log(
            hypothesis_id="H2",
            location="GamesService.checkers_move.after_user",
            message="After successful user move",
            data={
                "session_id": session_id,
                "current_player": game.current_player,
                "must_capture_from": game.must_capture_from,
            },
        )

        # Проверяем победу пользователя
        if game.winner == 1:
            state = game.get_board_state()
            self.finish_game_session(session_id, "win")
            return {
                "board": state["board"],
                "kings": state.get("kings"),
                "winner": "user",
                "game_over": True,
                "ai_move": None,
            }

        # КРИТИЧНО: Если есть обязательное взятие (множественное взятие),
        # пользователь должен продолжать ходить той же фишкой
        # Сохраняем состояние и возвращаем управление пользователю
        if game.must_capture_from:
            state = game.get_board_state()
            must_capture = list(game.must_capture_from) if game.must_capture_from else None
            self.update_game_session(
                session_id,
                {
                    "board": state["board"],
                    "kings": state.get("kings"),
                    "current_player": game.current_player,  # Остается 1 (пользователь)
                    "must_capture": must_capture,
                },
                "in_progress",
            )
            self.db.commit()
            return {
                "board": state["board"],
                "kings": state.get("kings"),
                "winner": None,
                "game_over": False,
                "ai_move": None,
            }

        # Ход AI (player = 2)
        # Получаем все возможные ходы для AI
        valid_moves = game.get_valid_moves(2)
        _debug_log(
            hypothesis_id="H3",
            location="GamesService.checkers_move.before_ai",
            message="Before AI move",
            data={
                "session_id": session_id,
                "current_player": game.current_player,
                "must_capture_from": game.must_capture_from,
                "ai_valid_moves_count": len(valid_moves),
            },
        )
        if not valid_moves:
            # AI не может сделать ход - пользователь победил
            state = game.get_board_state()
            self.finish_game_session(session_id, "win")
            return {
                "board": state["board"],
                "kings": state.get("kings"),
                "winner": "user",
                "game_over": True,
                "ai_move": None,
            }

        # Выбираем лучший ход через AI
        # Панда думает перед ходом
        await asyncio.sleep(1.5)
        # Конвертируем формат для старого AI
        frontend_board = game.get_board_state()["board"]
        ai_move = self.checkers_ai.get_best_move(frontend_board, "ai")

        if not ai_move:
            # AI не может сделать ход - пользователь победил
            state = game.get_board_state()
            self.finish_game_session(session_id, "win")
            return {
                "board": state["board"],
                "kings": state.get("kings"),
                "winner": "user",
                "game_over": True,
                "ai_move": None,
            }

        # Проверяем формат хода перед распаковкой
        if not isinstance(ai_move, tuple | list) or len(ai_move) != 4:
            logger.warning(
                f"⚠️ AI вернул невалидный формат хода: {ai_move}, используем первый валидный ход"
            )
            # Используем valid_moves, который уже получен выше
            # get_valid_moves возвращает List[Dict], нужно преобразовать в кортеж
            if valid_moves:
                first_move = valid_moves[0]
                if isinstance(first_move, dict):
                    from_pos = first_move.get("from", (0, 0))
                    to_pos = first_move.get("to", (0, 0))
                    ai_move = (from_pos[0], from_pos[1], to_pos[0], to_pos[1])
                elif isinstance(first_move, tuple | list) and len(first_move) == 4:
                    ai_move = first_move
                else:
                    logger.error(f"⚠️ Неожиданный формат хода в valid_moves: {first_move}")
                    ai_move = None
            else:
                # Нет валидных ходов - пользователь победил
                state = game.get_board_state()
                self.finish_game_session(session_id, "win")
                return {
                    "board": state["board"],
                    "kings": state.get("kings"),
                    "winner": "user",
                    "game_over": True,
                    "ai_move": None,
                }

        ai_from_row, ai_from_col, ai_to_row, ai_to_col = ai_move

        _debug_log(
            hypothesis_id="H3",
            location="GamesService.checkers_move.ai_chosen",
            message="AI move chosen",
            data={
                "session_id": session_id,
                "ai_move": [ai_from_row, ai_from_col, ai_to_row, ai_to_col],
            },
        )

        # Проверяем валидность хода AI перед выполнением
        valid_moves_ai = game.get_valid_moves(2)
        # get_valid_moves возвращает List[Dict] с форматом {'from': (r, c), 'to': (r, c), ...}
        ai_move_valid = any(
            move.get("from") == (ai_from_row, ai_from_col)
            and move.get("to") == (ai_to_row, ai_to_col)
            for move in valid_moves_ai
            if isinstance(move, dict)
        )

        if not ai_move_valid:
            # Ход AI невалидный - пробуем найти другой валидный ход
            if valid_moves_ai:
                # Берем первый валидный ход
                # get_valid_moves возвращает List[Dict] с форматом {'from': (r, c), 'to': (r, c), ...}
                first_move = valid_moves_ai[0]
                if isinstance(first_move, dict):
                    from_pos = first_move.get("from", (0, 0))
                    to_pos = first_move.get("to", (0, 0))
                    ai_from_row, ai_from_col = from_pos
                    ai_to_row, ai_to_col = to_pos
                elif isinstance(first_move, tuple | list) and len(first_move) == 4:
                    ai_from_row, ai_from_col, ai_to_row, ai_to_col = first_move
                else:
                    logger.error(f"⚠️ Неожиданный формат хода: {first_move}")
                    # Fallback - используем первый валидный ход из valid_moves
                    if valid_moves:
                        first_fallback = valid_moves[0]
                        if isinstance(first_fallback, dict):
                            from_pos = first_fallback.get("from", (0, 0))
                            to_pos = first_fallback.get("to", (0, 0))
                            ai_from_row, ai_from_col = from_pos
                            ai_to_row, ai_to_col = to_pos
                        else:
                            raise ValueError(
                                f"Неожиданный формат хода в valid_moves: {first_fallback}"
                            )
                    else:
                        raise ValueError("Нет валидных ходов для AI")
            else:
                # Нет валидных ходов - пользователь победил
                state = game.get_board_state()
                self.finish_game_session(session_id, "win")
                return {
                    "board": state["board"],
                    "kings": state.get("kings"),
                    "winner": "user",
                    "game_over": True,
                    "ai_move": None,
                }

        # Выполняем ход AI
        if game.make_move(ai_from_row, ai_from_col, ai_to_row, ai_to_col):
            _debug_log(
                hypothesis_id="H4",
                location="GamesService.checkers_move.after_ai",
                message="After AI move",
                data={
                    "session_id": session_id,
                    "current_player": game.current_player,
                    "must_capture_from": game.must_capture_from,
                },
            )
            # Проверяем победу AI
            if game.winner == 2:
                state = game.get_board_state()
                self.finish_game_session(session_id, "loss")
                return {
                    "board": state["board"],
                    "kings": state.get("kings"),
                    "winner": "ai",
                    "game_over": True,
                    "ai_move": (ai_from_row, ai_from_col, ai_to_row, ai_to_col),
                }
        else:
            # Ход AI не выполнен - пользователь победил
            state = game.get_board_state()
            self.finish_game_session(session_id, "win")
            return {
                "board": state["board"],
                "kings": state.get("kings"),
                "winner": "user",
                "game_over": True,
                "ai_move": None,
            }

        # Сохраняем состояние
        state = game.get_board_state()
        must_capture = list(state.get("must_capture")) if state.get("must_capture") else None
        self.update_game_session(
            session_id,
            {
                "board": state["board"],
                "kings": state.get("kings"),
                "current_player": game.current_player,
                "must_capture": must_capture,
            },
            "in_progress",
        )
        self.db.commit()

        return {
            "board": state["board"],
            "kings": state.get("kings"),
            "winner": None,
            "game_over": False,
            "ai_move": (ai_from_row, ai_from_col, ai_to_row, ai_to_col),
        }

    def game_2048_move(self, session_id: int, direction: str) -> dict:
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

        # Восстанавливаем или создаем игру
        if session.game_state and isinstance(session.game_state, dict):
            game_state = session.game_state
            board_data = game_state.get("board")
            if board_data and isinstance(board_data, list) and len(board_data) == 4:
                game = Game2048()
                game.board = [row[:] for row in board_data]
                game.score = game_state.get("score", 0)
                game.won = game_state.get("won", False)
                game.game_over = game_state.get("game_over", False)
            else:
                game = Game2048()
        else:
            game = Game2048()

        # Делаем ход
        if not game.move(direction):
            # Ход не изменил доску
            state = game.get_state()
            return {
                "board": state["board"],
                "score": state["score"],
                "game_over": state["game_over"],
                "won": state["won"],
            }

        state = game.get_state()

        # Проверяем поражение
        if state["game_over"]:
            self.finish_game_session(session_id, "loss", state["score"])
            self.db.commit()
            return {
                "board": state["board"],
                "score": state["score"],
                "game_over": True,
                "won": state["won"],
            }

        # Обновляем состояние
        self.update_game_session(
            session_id,
            {
                "board": state["board"],
                "score": state["score"],
                "won": state["won"],
                "game_over": state["game_over"],
            },
            "in_progress",
        )
        self.db.commit()

        return {
            "board": state["board"],
            "score": state["score"],
            "game_over": False,
            "won": state["won"],
        }

    def erudite_move(self, session_id: int, row: int, col: int, letter: str) -> dict:
        """
        Разместить фишку в Эрудите.

        Args:
            session_id: ID сессии
            row: Строка
            col: Колонка
            letter: Буква
        """
        session = self.db.get(GameSession, session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        # Восстанавливаем игру из сохранённого состояния
        if session.game_state and isinstance(session.game_state, dict):
            game = EruditeGame.from_dict(session.game_state)
        else:
            game = EruditeGame()

        # Размещаем фишку
        if not game.place_tile(row, col, letter):
            raise ValueError("Не удалось разместить фишку")

        state = game.get_state()

        # Обновляем сессию
        self.update_game_session(
            session_id,
            {
                "board": state["board"],
                "bonus_cells": state["bonus_cells"],
                "player_tiles": state["player_tiles"],
                "ai_tiles": state["ai_tiles"],
                "player_score": state["player_score"],
                "ai_score": state["ai_score"],
                "current_player": state["current_player"],
                "game_over": state["game_over"],
                "first_move": state["first_move"],
                "current_move": state["current_move"],
                "bag_count": state["bag_count"],
            },
            "loss" if state["game_over"] else "in_progress",
        )

        if state["game_over"]:
            self.finish_game_session(
                session_id,
                "loss" if state["player_score"] < state["ai_score"] else "win",
                state["player_score"],
            )
            self.db.commit()

        return state

    def erudite_clear_move(self, session_id: int) -> dict:
        """
        Очистить текущий ход в Эрудите.

        Args:
            session_id: ID сессии

        Returns:
            dict: Обновленное состояние игры
        """
        session = self.db.get(GameSession, session_id)
        if not session:
            raise ValueError("Session not found")

        game = EruditeGame.from_dict(session.game_state)
        game.clear_move()
        state = game.get_state()

        session.game_state = {
            "board": state["board"],
            "bonus_cells": state["bonus_cells"],
            "player_tiles": state["player_tiles"],
            "ai_tiles": state["ai_tiles"],
            "player_score": state["player_score"],
            "ai_score": state["ai_score"],
            "current_player": state["current_player"],
            "game_over": state["game_over"],
            "first_move": state["first_move"],
            "current_move": state["current_move"],
            "bag_count": state["bag_count"],
        }

        self.db.flush()
        return state

    def erudite_confirm_move(self, session_id: int) -> dict:
        """Подтвердить ход в Эрудите."""
        session = self.db.get(GameSession, session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        if session.game_state and isinstance(session.game_state, dict):
            game = EruditeGame.from_dict(session.game_state)
        else:
            game = EruditeGame()

        success, message = game.make_move()
        if not success:
            raise ValueError(message)

        state = game.get_state()

        self.update_game_session(
            session_id,
            {
                "board": state["board"],
                "bonus_cells": state["bonus_cells"],
                "player_tiles": state["player_tiles"],
                "ai_tiles": state["ai_tiles"],
                "player_score": state["player_score"],
                "ai_score": state["ai_score"],
                "current_player": state["current_player"],
                "game_over": state["game_over"],
                "first_move": state["first_move"],
                "current_move": state["current_move"],
                "bag_count": state["bag_count"],
            },
            "loss" if state["game_over"] else "in_progress",
        )

        if state["game_over"]:
            self.finish_game_session(
                session_id,
                "loss" if state["player_score"] < state["ai_score"] else "win",
                state["player_score"],
            )
            self.db.commit()

        return state
