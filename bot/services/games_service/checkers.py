"""Логика игры в шашки."""

import random

from loguru import logger

from bot.models import GameSession
from bot.services.game_ai import _debug_log
from bot.services.game_engines import CheckersGame


def _evaluate_board(game: CheckersGame) -> float:
    """Оценка позиции для AI (игрок 2). Больше = лучше для AI."""
    score = 0.0
    for r in range(8):
        for c in range(8):
            piece = game.board[r][c]
            if piece == 0:
                continue
            # Простая шашка: +/-1, дамка: +/-3
            if piece == 2:  # AI простая
                score += 1.0
                # Продвижение AI к дамке (вниз, к ряду 7)
                score += r * 0.15
                # Контроль центра
                if 2 <= r <= 5 and 2 <= c <= 5:
                    score += 0.3
            elif piece == 4:  # AI дамка
                score += 3.0
                if 2 <= r <= 5 and 2 <= c <= 5:
                    score += 0.5
            elif piece == 1:  # Игрок простая
                score -= 1.0
                score -= (7 - r) * 0.15
                if 2 <= r <= 5 and 2 <= c <= 5:
                    score -= 0.3
            elif piece == 3:  # Игрок дамка
                score -= 3.0
                if 2 <= r <= 5 and 2 <= c <= 5:
                    score -= 0.5
    return score


def _select_best_ai_move(game: CheckersGame, valid_moves: list[dict]) -> dict:
    """Выбрать лучший ход для AI на основе оценки позиции после хода."""
    # Обязательные взятия имеют приоритет
    capture_moves = [m for m in valid_moves if m.get("capture")]
    candidates = capture_moves if capture_moves else valid_moves

    if len(candidates) == 1:
        return candidates[0]

    best_move = candidates[0]
    best_score = float("-inf")

    # Сохраняем состояние доски
    saved_board = [row[:] for row in game.board]
    saved_player = game.current_player
    saved_winner = game.winner
    saved_capture = game.must_capture_from

    for move_data in candidates:
        fr, fc = move_data["from"][0], move_data["from"][1]
        tr, tc = move_data["to"][0], move_data["to"][1]

        # Пробуем ход
        game.make_move(fr, fc, tr, tc)
        score = _evaluate_board(game)

        # Откат
        game.board = [row[:] for row in saved_board]
        game.current_player = saved_player
        game.winner = saved_winner
        game.must_capture_from = saved_capture

        if score > best_score:
            best_score = score
            best_move = move_data

    return best_move


def _load_checkers_game(session: GameSession) -> CheckersGame:
    """Восстановить CheckersGame из сохранённого состояния сессии."""
    if session.game_state and isinstance(session.game_state, dict):
        game_state = session.game_state
        board_data = game_state.get("board")
        if board_data and isinstance(board_data, list) and len(board_data) == 8:
            game = CheckersGame()
            kings_data = game_state.get("kings", [])
            # Конвертируем frontend формат ('user', 'ai', None) в engine формат (1, 2, 0, 3, 4)
            for r in range(8):
                for c in range(8):
                    cell = (
                        board_data[r][c] if r < len(board_data) and c < len(board_data[r]) else None
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
            game.current_player = game_state.get("current_player", 1)
            must_capture = game_state.get("must_capture")
            if must_capture and isinstance(must_capture, list) and len(must_capture) == 2:
                game.must_capture_from = tuple(must_capture)
            game.winner = game_state.get("winner")
            return game
    return CheckersGame()


class CheckersMixin:
    """Mixin: шашки."""

    def get_checkers_valid_moves(self, session_id: int) -> dict:
        """
        Получить валидные ходы для пользователя в шашках и текущего игрока.

        Args:
            session_id: ID сессии

        Returns:
            dict: {"valid_moves": [...], "current_player": 1|2}. current_player=2 — очередь AI.
        """
        session = self.db.get(GameSession, session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        game = _load_checkers_game(session)

        # КРИТИЧНО: Если очередь AI — возвращаем пустой список и current_player=2,
        # чтобы фронт показал «Ход соперника» и не показывал «Эта фишка не может ходить»
        if game.current_player != 1:
            logger.warning(
                f"⚠️ Попытка получить ходы для пользователя, но очередь AI (current_player={game.current_player})"
            )
            return {"valid_moves": [], "current_player": game.current_player}

        # Получаем валидные ходы для пользователя (player = 1)
        raw = game.get_valid_moves(1)

        _debug_log(
            hypothesis_id="H1",
            location="GamesService.get_checkers_valid_moves",
            message="Calculated valid moves for user",
            data={
                "session_id": session_id,
                "current_player": game.current_player,
                "must_capture_from": game.must_capture_from,
                "valid_moves_count": len(raw),
            },
        )
        # JSON-сериализуемый формат: list вместо tuple (from/to/capture)
        valid_moves = [
            {
                "from": [m["from"][0], m["from"][1]],
                "to": [m["to"][0], m["to"][1]],
                "capture": [m["capture"][0], m["capture"][1]] if m["capture"] else None,
            }
            for m in raw
        ]
        return {"valid_moves": valid_moves, "current_player": game.current_player}

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

        game = _load_checkers_game(session)

        # КРИТИЧНО: Проверяем, что очередь пользователя
        if game.current_player != 1:
            logger.warning(
                f"⚠️ Попытка хода пользователя, но очередь AI (current_player={game.current_player})"
            )
            raise ValueError("Не ваша очередь ходить")

        # Ход пользователя (player = 1)
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

        # Выбираем лучший ход через оценку позиции
        ai_move_data = _select_best_ai_move(game, valid_moves)

        ai_move = (
            ai_move_data["from"][0],
            ai_move_data["from"][1],
            ai_move_data["to"][0],
            ai_move_data["to"][1],
        )

        if not ai_move_data:
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
        last_ai_move = (ai_from_row, ai_from_col, ai_to_row, ai_to_col)

        _debug_log(
            hypothesis_id="H3",
            location="GamesService.checkers_move.ai_chosen",
            message="AI move chosen",
            data={
                "session_id": session_id,
                "ai_move": [ai_from_row, ai_from_col, ai_to_row, ai_to_col],
            },
        )

        # Выполняем ход AI (и цикл множественного взятия)
        if not game.make_move(ai_from_row, ai_from_col, ai_to_row, ai_to_col):
            state = game.get_board_state()
            self.finish_game_session(session_id, "win")
            return {
                "board": state["board"],
                "kings": state.get("kings"),
                "winner": "user",
                "game_over": True,
                "ai_move": None,
            }

        while game.winner is None and game.must_capture_from:
            # AI должен продолжать бить (множественное взятие)
            next_moves = game.get_valid_moves(2)
            capture_moves = [m for m in next_moves if m.get("capture")]
            if not capture_moves:
                break
            ai_move_data = random.choice(capture_moves)
            af, ac = ai_move_data["from"][0], ai_move_data["from"][1]
            at_row, at_col = ai_move_data["to"][0], ai_move_data["to"][1]
            last_ai_move = (af, ac, at_row, at_col)
            if not game.make_move(af, ac, at_row, at_col):
                break

        _debug_log(
            hypothesis_id="H4",
            location="GamesService.checkers_move.after_ai",
            message="After AI move(s)",
            data={
                "session_id": session_id,
                "current_player": game.current_player,
                "must_capture_from": game.must_capture_from,
            },
        )

        if game.winner == 2:
            state = game.get_board_state()
            self.finish_game_session(session_id, "loss")
            return {
                "board": state["board"],
                "kings": state.get("kings"),
                "winner": "ai",
                "game_over": True,
                "ai_move": last_ai_move,
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
            "ai_move": last_ai_move,
        }

    async def checkers_run_ai_turn(self, session_id: int) -> dict:
        """
        Выполнить ход(ы) панды, когда очередь AI (current_player=2).
        Используется при загрузке сессии, чтобы разблокировать «Ход панды».
        """
        session = self.db.get(GameSession, session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        game = _load_checkers_game(session)
        if game.current_player != 2:
            state = game.get_board_state()
            winner = "user" if game.winner == 1 else ("ai" if game.winner == 2 else None)
            return {
                "board": state["board"],
                "kings": state.get("kings"),
                "winner": winner,
                "game_over": game.winner is not None,
                "ai_move": None,
            }

        valid_moves = game.get_valid_moves(2)
        if not valid_moves:
            state = game.get_board_state()
            self.finish_game_session(session_id, "win")
            return {
                "board": state["board"],
                "kings": state.get("kings"),
                "winner": "user",
                "game_over": True,
                "ai_move": None,
            }

        ai_move_data = _select_best_ai_move(game, valid_moves)
        af, ac = ai_move_data["from"][0], ai_move_data["from"][1]
        at_row, at_col = ai_move_data["to"][0], ai_move_data["to"][1]
        last_ai_move = (af, ac, at_row, at_col)
        if not game.make_move(af, ac, at_row, at_col):
            state = game.get_board_state()
            self.finish_game_session(session_id, "win")
            return {
                "board": state["board"],
                "kings": state.get("kings"),
                "winner": "user",
                "game_over": True,
                "ai_move": None,
            }

        while game.winner is None and game.must_capture_from:
            next_moves = game.get_valid_moves(2)
            capture_moves = [m for m in next_moves if m.get("capture")]
            if not capture_moves:
                break
            ai_move_data = random.choice(capture_moves)
            af, ac = ai_move_data["from"][0], ai_move_data["from"][1]
            at_row, at_col = ai_move_data["to"][0], ai_move_data["to"][1]
            last_ai_move = (af, ac, at_row, at_col)
            if not game.make_move(af, ac, at_row, at_col):
                break

        if game.winner == 2:
            state = game.get_board_state()
            self.finish_game_session(session_id, "loss")
            return {
                "board": state["board"],
                "kings": state.get("kings"),
                "winner": "ai",
                "game_over": True,
                "ai_move": last_ai_move,
            }

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
            "ai_move": last_ai_move,
        }

    def _checkers_load_game_from_session(self, session: "GameSession") -> CheckersGame:
        """Восстановить CheckersGame из сохранённого состояния сессии."""
        return _load_checkers_game(session)
