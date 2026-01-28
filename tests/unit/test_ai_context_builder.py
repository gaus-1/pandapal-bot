"""
Тесты для ContextBuilder
Тестирование построения контекста для AI
"""

import pytest

from bot.services.ai_context_builder import ContextBuilder


class TestContextBuilder:
    """Тесты для построения контекста"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.builder = ContextBuilder()

    def test_basic_context(self):
        """Тест базового контекста"""
        user_message = "Привет!"
        context = self.builder.build(user_message)

        assert "Текущий вопрос: Привет!" in context
        assert len(context) > 0

    def test_age_context_young(self):
        """Тест контекста для маленьких детей"""
        user_message = "Что такое солнце?"
        context = self.builder.build(user_message, user_age=7)

        assert "ребенок 6-7 лет" in context or "ребенок 8-9 лет" in context
        assert "простыми словами" in context or "простые слова" in context
        assert "Текущий вопрос: Что такое солнце?" in context

    def test_age_context_middle(self):
        """Тест контекста для средних детей"""
        user_message = "Объясни физику"
        context = self.builder.build(user_message, user_age=10)

        assert "ребенок 10-11 лет" in context or "ребенок 8-9 лет" in context
        assert "примеры" in context or "термины" in context
        assert "Текущий вопрос: Объясни физику" in context

    def test_age_context_teen(self):
        """Тест контекста для подростков"""
        user_message = "Расскажи про квантовую физику"
        context = self.builder.build(user_message, user_age=15)

        assert "подросток 14-15 лет" in context or "подросток 12-13 лет" in context
        assert "сложные" in context or "научные" in context or "развернутые" in context
        assert "Текущий вопрос: Расскажи про квантовую физику" in context

    def test_history_context(self):
        """Тест контекста с историей"""
        user_message = "А что дальше?"
        chat_history = [
            {"role": "user", "content": "Привет"},
            {"role": "ai", "content": "Привет! Как дела?"},
            {"role": "user", "content": "Расскажи про математику"},
        ]

        context = self.builder.build(user_message, chat_history)

        assert "Предыдущие сообщения:" in context
        assert "Пользователь: Привет" in context
        assert "AI: Привет! Как дела?" in context
        assert "Пользователь: Расскажи про математику" in context
        assert "Текущий вопрос: А что дальше?" in context

    def test_history_limit(self):
        """Тест ограничения истории (только последние 5)"""
        user_message = "Вопрос"
        chat_history = []
        for i in range(10):  # 10 сообщений
            chat_history.extend(
                [
                    {"role": "user", "content": f"Вопрос {i}"},
                    {"role": "ai", "content": f"Ответ {i}"},
                ]
            )

        context = self.builder.build(user_message, chat_history)

        # Проверяем что контекст содержит предыдущие сообщения
        assert "Предыдущие сообщения:" in context
        assert len(context) > 0

    def test_combined_context(self):
        """Тест комбинированного контекста"""
        user_message = "Спасибо!"
        chat_history = [
            {"role": "user", "content": "Помоги с задачей"},
            {"role": "ai", "content": "Конечно! Какую задачу?"},
        ]

        context = self.builder.build(user_message, chat_history, user_age=12)

        assert "подросток 12-13 лет" in context or "ребенок 10-11 лет" in context
        assert "примеры" in context or "термины" in context or "объяснения" in context
        assert "Предыдущие сообщения:" in context
        assert "Пользователь: Помоги с задачей" in context
        assert "AI: Конечно! Какую задачу?" in context
        assert "Текущий вопрос: Спасибо!" in context

    def test_empty_history(self):
        """Тест с пустой историей"""
        user_message = "Первый вопрос"
        context = self.builder.build(user_message, chat_history=None)

        assert "Текущий вопрос: Первый вопрос" in context
        assert "Предыдущие сообщения:" not in context

    def test_empty_message(self):
        """Тест с пустым сообщением"""
        context = self.builder.build("")

        assert "Текущий вопрос: " in context
        assert len(context) > 0
