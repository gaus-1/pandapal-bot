"""Логика игры Эрудит."""

from loguru import logger

from bot.models import GameSession
from bot.services.game_engines import EruditeGame


class EruditeMixin:
    """Mixin: Эрудит."""

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

        # Нормализуем букву (фишки в игре — заглавные; джокер не трогаем)
        letter_normalized = letter.upper() if letter and letter != "*" else letter
        if not game.place_tile(row, col, letter_normalized):
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

        # Если игра не окончена и теперь ход AI - делаем ход AI
        if not game.game_over and game.current_player == 2:
            ai_success, ai_message = game.make_ai_move()
            logger.info(f"AI ход в Эрудите: {ai_message}")

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
                "bag": game.bag,  # Сохраняем bag для восстановления
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
