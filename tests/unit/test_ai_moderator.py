"""
Тесты для ContentModerator
Тестирование модерации контента
"""

import pytest

from bot.services.ai_moderator import ContentModerator


class TestContentModerator:
    """Тесты для модерации контента"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.moderator = ContentModerator()

    def test_safe_content(self):
        """Тест безопасного контента"""
        safe_texts = [
            "Привет! Как дела?",
            "Помоги с математикой",
            "Что такое фотосинтез?",
            "Расскажи про космос",
            "Как решить уравнение?",
        ]

        for text in safe_texts:
            is_safe, reason = self.moderator.moderate(text)
            assert is_safe is True
            assert reason.lower() == "контент безопасен"

    def test_forbidden_content(self):
        """Тест запрещенного контента"""
        forbidden_texts = [
            "как курить",
            "где купить наркотики",
            "как убить человека",
            "секс с детьми",
            "где взять оружие",
        ]

        for text in forbidden_texts:
            is_safe, reason = self.moderator.moderate(text)
            assert is_safe is False
            assert "запрещен" in reason.lower() or "запрещён" in reason.lower()

    def test_case_insensitive(self):
        """Тест нечувствительности к регистру"""
        text = "КАК КУРИТЬ"
        is_safe, reason = self.moderator.moderate(text)
        assert is_safe is False
        assert "запрещен" in reason.lower() or "запрещён" in reason.lower()

    def test_empty_text(self):
        """Тест пустого текста"""
        is_safe, reason = self.moderator.moderate("")
        assert is_safe is True
        assert reason.lower() == "контент безопасен"

    def test_edge_cases(self):
        """Тест граничных случаев"""
        edge_cases = [
            " ",  # Только пробел
            "\n\t",  # Только переносы
            "123456789",  # Только цифры
            "!@#$%^&*()",  # Только символы
        ]

        for text in edge_cases:
            is_safe, reason = self.moderator.moderate(text)
            assert is_safe is True
            assert reason.lower() == "контент безопасен"
