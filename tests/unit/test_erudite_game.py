"""
Unit-тесты для игры Эрудит.
Проверка первого хода через центр, валидации, round-trip через from_dict.
"""

import json

import pytest

from bot.services.game_engines import EruditeGame


class TestEruditeFirstMoveCenter:
    """Первый ход должен проходить через центр (7,7)."""

    def test_first_move_through_center_horizontal(self):
        """Слово ДОМ горизонтально через центр: (7,6),(7,7),(7,8) — успех."""
        game = EruditeGame()
        game.player_tiles = ["Д", "О", "М"]
        game.current_player = 1
        game.first_move = True

        assert game.place_tile(7, 6, "Д") is True
        assert game.place_tile(7, 7, "О") is True
        assert game.place_tile(7, 8, "М") is True

        ok, msg = game.validate_move()
        assert ok, msg
        success, err = game.make_move()
        assert success, err
        assert game.first_move is False

    def test_first_move_through_center_vertical(self):
        """Слово ГОД вертикально через центр: (6,7),(7,7),(8,7) — успех."""
        game = EruditeGame()
        game.player_tiles = ["Г", "О", "Д"]
        game.current_player = 1
        game.first_move = True

        assert game.place_tile(6, 7, "Г") is True
        assert game.place_tile(7, 7, "О") is True
        assert game.place_tile(8, 7, "Д") is True

        ok, msg = game.validate_move()
        assert ok, msg
        success, err = game.make_move()
        assert success, err

    def test_first_move_not_through_center_fails(self):
        """Первый ход мимо центра — ошибка. Слово КОТ на (7,4),(7,5),(7,6), центр (7,7) не задействован."""
        game = EruditeGame()
        game.player_tiles = ["К", "О", "Т"]
        game.current_player = 1
        game.first_move = True

        game.place_tile(7, 4, "К")
        game.place_tile(7, 5, "О")
        game.place_tile(7, 6, "Т")
        ok, msg = game.validate_move()
        assert not ok, msg
        assert "центр" in msg.lower()

    def test_first_move_roundtrip_from_dict_then_confirm(self):
        """Place -> get_state -> JSON -> from_dict -> make_move: центр сохраняется."""
        game = EruditeGame()
        game.player_tiles = ["Д", "О", "М"]
        game.current_player = 1
        game.first_move = True

        game.place_tile(7, 6, "Д")
        game.place_tile(7, 7, "О")
        game.place_tile(7, 8, "М")

        state = game.get_state()
        # Имитация БД: current_move как list of lists (JSON)
        state["current_move"] = [list(t) for t in state["current_move"]]
        state_json = json.dumps(state)
        state_loaded = json.loads(state_json)

        restored = EruditeGame.from_dict(state_loaded)
        assert restored.first_move is True
        assert len(restored.current_move) == 3

        ok, msg = restored.validate_move()
        assert ok, msg
        success, err = restored.make_move()
        assert success, err
