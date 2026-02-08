"""Логика игры 2048."""

from bot.models import GameSession
from bot.services.game_engines import Game2048


class Game2048Mixin:
    """Mixin: 2048."""

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
