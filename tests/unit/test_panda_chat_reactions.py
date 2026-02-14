"""
Unit-тесты реакций панды в чате (get_chat_reaction).

Без реального API: проверка выбора реакции по фразам из конфига.
"""

import pytest

from bot.config.panda_chat_reactions_data import (
    NEGATIVE_PHRASES,
    POSITIVE_PHRASES,
    REACTIONS_NEGATIVE,
    REACTIONS_POSITIVE,
)
from bot.services.panda_chat_reactions import get_chat_reaction


class TestGetChatReaction:
    """Тесты get_chat_reaction."""

    def test_positive_phrase_returns_happy_or_eating(self):
        """Позитивная фраза -> одна из happy, eating."""
        phrase = next(iter(POSITIVE_PHRASES))
        result = get_chat_reaction(phrase)
        assert result in REACTIONS_POSITIVE

    def test_positive_single_word_returns_positive_reaction(self):
        """Одно слово позитива -> happy или eating."""
        phrase = next(p for p in POSITIVE_PHRASES if len(p) <= 10)
        result = get_chat_reaction(phrase)
        assert result in REACTIONS_POSITIVE

    def test_negative_phrase_returns_offended_or_questioning(self):
        """Негативная фраза -> одна из offended, questioning (фраза без вхождения позитива)."""
        phrase = "плохо"  # только негатив, не содержит подстроку из POSITIVE
        assert phrase in NEGATIVE_PHRASES
        result = get_chat_reaction(phrase)
        assert result in REACTIONS_NEGATIVE

    def test_negative_single_word_returns_negative_reaction(self):
        """Одно слово негатива -> offended или questioning."""
        phrase = "ошибка"  # только негатив
        assert phrase in NEGATIVE_PHRASES
        result = get_chat_reaction(phrase)
        assert result in REACTIONS_NEGATIVE

    def test_neutral_message_returns_none(self):
        """Нейтральное учебное сообщение -> None."""
        result = get_chat_reaction("kak reshit uravnenie 2x plus 5 equals 13")
        assert result is None

    def test_empty_string_returns_none(self):
        """Пустая строка -> None."""
        assert get_chat_reaction("") is None

    def test_whitespace_only_returns_none(self):
        """Только пробелы -> None."""
        assert get_chat_reaction("   \n  ") is None

    def test_mixed_positive_and_negative_returns_none(self):
        """Позитив и негатив вместе -> None: есть фраза из обоих наборов."""
        pos_phrase = next(iter(POSITIVE_PHRASES))
        neg_phrase = next(iter(NEGATIVE_PHRASES))
        result = get_chat_reaction(f"{pos_phrase} i {neg_phrase}")
        assert result is None

    def test_none_input_returns_none(self):
        """None на входе -> None."""
        assert get_chat_reaction(None) is None

    def test_case_insensitive_positive(self):
        """Регистр не важен для позитива."""
        phrase = next(iter(POSITIVE_PHRASES))
        result = get_chat_reaction(phrase.upper())
        assert result in REACTIONS_POSITIVE

    def test_case_insensitive_negative(self):
        """Регистр не важен для негатива."""
        phrase = "ошибка"
        result = get_chat_reaction(phrase.upper())
        assert result in REACTIONS_NEGATIVE

    def test_uses_phrases_from_config_positive(self):
        """Используются фразы из POSITIVE_PHRASES."""
        for phrase in list(POSITIVE_PHRASES)[:3]:
            result = get_chat_reaction(phrase)
            assert result in REACTIONS_POSITIVE, f"Фраза из конфига: {phrase}"

    def test_uses_phrases_from_config_negative(self):
        """Используются фразы из NEGATIVE_PHRASES: хотя бы одна даёт реакцию."""
        results = [get_chat_reaction(p) for p in list(NEGATIVE_PHRASES)[:5]]
        assert any(r in REACTIONS_NEGATIVE for r in results), (
            "Хотя бы одна из фраз NEGATIVE_PHRASES должна дать offended или questioning"
        )
