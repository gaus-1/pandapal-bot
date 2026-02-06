"""Unit-тесты сервиса предпочтений по эмодзи в ответах Панды."""

import pytest

from bot.services.emoji_preference import (
    compute_allow_emoji_this_turn,
    get_emoji_prompt_snippet,
    parse_emoji_preference_from_message,
)


class TestParseEmojiPreferenceFromMessage:
    """Тесты парсинга предпочтения по эмодзи из сообщения."""

    @pytest.mark.unit
    def test_no_emoji_phrases(self):
        """Фразы «не использовать эмодзи» возвращают False."""
        for msg in [
            "не ставь эмодзи",
            "без эмодзи пожалуйста",
            "не используй смайлики в ответах",
            "не надо эмодзи",
        ]:
            assert parse_emoji_preference_from_message(msg) is False

    @pytest.mark.unit
    def test_yes_emoji_phrases(self):
        """Фразы «добавлять эмодзи» возвращают True."""
        for msg in [
            "добавляй эмодзи",
            "ставь эмодзи в ответах",
            "можно эмодзи",
            "хочу эмодзи",
        ]:
            assert parse_emoji_preference_from_message(msg) is True

    @pytest.mark.unit
    def test_no_preference_returns_none(self):
        """Обычные сообщения без просьбы возвращают None."""
        for msg in [
            "реши уравнение",
            "расскажи про фотосинтез",
            "",
        ]:
            assert parse_emoji_preference_from_message(msg) is None

    @pytest.mark.unit
    def test_empty_or_invalid(self):
        """Пустая строка и нестрока возвращают None."""
        assert parse_emoji_preference_from_message("") is None
        assert parse_emoji_preference_from_message(None) is None


class TestComputeAllowEmojiThisTurn:
    """Тесты решения «разрешить эмодзи в этом ответе» (2 из 7)."""

    @pytest.mark.unit
    def test_empty_history_allows(self):
        """Пустая история — разрешаем (первый ответ)."""
        assert compute_allow_emoji_this_turn([]) is True

    @pytest.mark.unit
    def test_two_out_of_seven(self):
        """Эмодзи разрешены в 2 из каждых 7 ответов ассистента (count % 7 in (2, 5))."""
        for count in (2, 5):
            history = [{"role": "assistant"}] * count
            assert compute_allow_emoji_this_turn(history) is True
        for count in (1, 3, 4, 6):
            history = [{"role": "assistant"}] * count
            assert compute_allow_emoji_this_turn(history) is False


class TestGetEmojiPromptSnippet:
    """Тесты фрагмента системного промпта про эмодзи."""

    @pytest.mark.unit
    def test_no_emoji_returns_instruction(self):
        """emoji_in_chat=False — инструкция не использовать эмодзи."""
        s = get_emoji_prompt_snippet(False, True)
        assert s is not None
        assert "не используй" in s.lower() or "не используй" in s
        assert "структура" in s.lower()

    @pytest.mark.unit
    def test_yes_emoji_returns_instruction(self):
        """emoji_in_chat=True — инструкция добавлять 1–2 эмодзи."""
        s = get_emoji_prompt_snippet(True, True)
        assert s is not None
        assert "украшение" in s.lower()
        assert "структура" in s.lower()

    @pytest.mark.unit
    def test_default_allow_this_turn(self):
        """emoji_in_chat=None, allow_this_turn=True — можно в этом ответе."""
        s = get_emoji_prompt_snippet(None, True)
        assert s is not None
        assert "можно" in s.lower() or "добавить" in s.lower()
        assert "структура" in s.lower()

    @pytest.mark.unit
    def test_default_disallow_this_turn(self):
        """emoji_in_chat=None, allow_this_turn=False — не использовать в этом ответе."""
        s = get_emoji_prompt_snippet(None, False)
        assert s is not None
        assert "не используй" in s.lower() or "эмодзи не" in s
        assert "структура" in s.lower()
