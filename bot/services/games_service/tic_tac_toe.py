"""Логика игры крестики-нолики."""

import asyncio

from bot.models import GameSession
from bot.services.game_engines import TicTacToe


class TicTacToeMixin:
    """Mixin: крестики-нолики."""

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
