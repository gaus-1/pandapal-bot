"""
Unit-тесты для игры Эрудит.
Проверка первого хода через центр, валидации, round-trip через from_dict,
словаря и формирования фишек.
"""

import json

import pytest

from bot.services.erudite_dictionary import ERUDITE_DICTIONARY, is_valid_word
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


class TestEruditeDictionary:
    """Словарь: валидация слов."""

    def test_valid_words_from_dictionary(self):
        """Слова из словаря принимаются (регистр не важен)."""
        assert is_valid_word("дом") is True
        assert is_valid_word("ДОМ") is True
        assert is_valid_word("  кот  ") is True
        assert is_valid_word("школа") is True
        assert is_valid_word("год") is True

    def test_invalid_words_rejected(self):
        """Слова не из словаря отклоняются."""
        assert is_valid_word("абв") is False
        assert is_valid_word("xyz") is False
        assert is_valid_word("") is False

    def test_dictionary_has_expected_size(self):
        """Словарь не пустой и содержит базовый набор."""
        assert len(ERUDITE_DICTIONARY) >= 100
        assert "дом" in ERUDITE_DICTIONARY
        assert "кот" in ERUDITE_DICTIONARY


class TestEruditeTiles:
    """Формирование фишек для пользователя и AI."""

    def test_bag_total_count(self):
        """После раздачи в мешке остаётся total - 14 фишек (7 игроку + 7 AI)."""
        game = EruditeGame()
        total = sum(game.LETTER_COUNTS.values())
        expected_in_bag = total - 2 * EruditeGame.TILES_PER_PLAYER
        assert len(game.bag) == expected_in_bag

    def test_player_and_ai_get_seven_tiles_each(self):
        """При инициализации игрок и AI получают по 7 фишек."""
        game = EruditeGame()
        assert len(game.player_tiles) == EruditeGame.TILES_PER_PLAYER
        assert len(game.ai_tiles) == EruditeGame.TILES_PER_PLAYER

    def test_tiles_are_uppercase_from_bag(self):
        """Фишки в руке — заглавные буквы (как в мешке)."""
        game = EruditeGame()
        for letter in game.player_tiles:
            assert letter == letter.upper() or letter == "*"
        for letter in game.ai_tiles:
            assert letter == letter.upper() or letter == "*"

    def test_get_state_returns_player_tiles_for_frontend(self):
        """get_state отдаёт player_tiles для отображения на фронте."""
        game = EruditeGame()
        state = game.get_state()
        assert "player_tiles" in state
        assert len(state["player_tiles"]) == EruditeGame.TILES_PER_PLAYER
        assert state["player_tiles"] == game.player_tiles


class TestEruditeValidation:
    """Валидация хода: словарь, отклонение неверных слов."""

    def test_word_not_in_dictionary_fails_validation(self):
        """Ход, образующий слово не из словаря, не проходит валидацию."""
        game = EruditeGame()
        game.player_tiles = ["А", "Б", "В"]
        game.current_player = 1
        game.first_move = True
        game.place_tile(7, 6, "А")
        game.place_tile(7, 7, "Б")
        game.place_tile(7, 8, "В")
        ok, msg = game.validate_move()
        assert not ok
        assert "словаре" in msg.lower() or "не найдено" in msg.lower()

    def test_place_tile_requires_letter_from_hand(self):
        """Нельзя поставить букву, которой нет в руке."""
        game = EruditeGame()
        game.player_tiles = ["Д", "О", "М"]
        game.current_player = 1
        assert game.place_tile(7, 7, "К") is False
        assert game.place_tile(7, 7, "Д") is True
