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
    """Тесты решения «разрешить эмодзи в этом ответе» — всегда True."""

    @pytest.mark.unit
    def test_empty_history_allows(self):
        """Пустая история — разрешаем."""
        assert compute_allow_emoji_this_turn([]) is True

    @pytest.mark.unit
    def test_always_allows(self):
        """Эмодзи разрешены в каждом ответе."""
        for count in (1, 2, 3, 4, 5, 6, 10):
            history = [{"role": "assistant"}] * count
            assert compute_allow_emoji_this_turn(history) is True


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
        """emoji_in_chat=True — обязательно добавить 1–2 эмодзи."""
        s = get_emoji_prompt_snippet(True, True)
        assert s is not None
        assert "обязательно" in s.lower()
        assert "1–2" in s
        assert "структура" in s.lower()

    @pytest.mark.unit
    def test_default_same_as_yes(self):
        """emoji_in_chat=None — поведение как True (эмодзи по умолчанию включены)."""
        s_none = get_emoji_prompt_snippet(None, True)
        s_true = get_emoji_prompt_snippet(True, True)
        assert s_none == s_true

    @pytest.mark.unit
    def test_default_ignores_allow_flag(self):
        """emoji_in_chat=None — allow_emoji_this_turn не влияет (всегда включены)."""
        s_allow = get_emoji_prompt_snippet(None, True)
        s_disallow = get_emoji_prompt_snippet(None, False)
        assert s_allow == s_disallow
