"""
Юнит-тесты для PromptBuilder: текущая тема в системном промпте.
"""

import pytest

from bot.services.prompt_builder import PromptBuilder


class TestCurrentTopicSnippet:
    """Блок «текущая тема» в build_system_prompt."""

    def test_no_history_no_current_topic(self):
        """Без истории в промпте нет подстроки «Текущий контекст»."""
        builder = PromptBuilder()
        prompt = builder.build_system_prompt(chat_history=[])
        assert "Текущий контекст" not in prompt

    def test_history_without_assistant_no_current_topic(self):
        """Только user-сообщения — блока текущей темы нет."""
        builder = PromptBuilder()
        prompt = builder.build_system_prompt(
            chat_history=[{"role": "user", "text": "Привет"}]
        )
        assert "Текущий контекст" not in prompt

    def test_history_with_assistant_has_current_topic(self):
        """При истории user + assistant в промпте есть «Текущий контекст» и фрагмент ответа."""
        builder = PromptBuilder()
        last_reply = "Фотосинтез — это процесс, при котором растения получают энергию из света."
        prompt = builder.build_system_prompt(
            chat_history=[
                {"role": "user", "text": "Что такое фотосинтез?"},
                {"role": "assistant", "text": last_reply},
            ]
        )
        assert "Текущий контекст" in prompt
        assert "Фотосинтез" in prompt
        assert last_reply[:50] in prompt or "фотосинтез" in prompt.lower()

    def test_current_topic_truncated_at_newline(self):
        """Фрагмент берётся до первого перевода строки."""
        builder = PromptBuilder()
        first_line = "Первый абзац ответа."
        full_text = first_line + "\n\nВторой абзац."
        prompt = builder.build_system_prompt(
            chat_history=[
                {"role": "user", "text": "?"},
                {"role": "assistant", "text": full_text},
            ]
        )
        assert "Текущий контекст" in prompt
        assert first_line in prompt
        assert "Второй абзац" not in prompt
