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
        
        assert "ребенок 6-8 лет" in context
        assert "простыми словами" in context
        assert "Текущий вопрос: Что такое солнце?" in context
    
    def test_age_context_middle(self):
        """Тест контекста для средних детей"""
        user_message = "Объясни физику"
        context = self.builder.build(user_message, user_age=10)
        
        assert "ребенок 9-12 лет" in context
        assert "понятные примеры" in context
        assert "Текущий вопрос: Объясни физику" in context
    
    def test_age_context_teen(self):
        """Тест контекста для подростков"""
        user_message = "Расскажи про квантовую физику"
        context = self.builder.build(user_message, user_age=15)
        
        assert "подросток 13-18 лет" in context
        assert "более сложные объяснения" in context
        assert "Текущий вопрос: Расскажи про квантовую физику" in context
    
    def test_history_context(self):
        """Тест контекста с историей"""
        user_message = "А что дальше?"
        chat_history = [
            {"role": "user", "content": "Привет"},
            {"role": "ai", "content": "Привет! Как дела?"},
            {"role": "user", "content": "Расскажи про математику"}
        ]
        
        context = self.builder.build(user_message, chat_history)
        
        assert "Предыдущие сообщения:" in context
        assert "user: Привет" in context
        assert "ai: Привет! Как дела?" in context
        assert "user: Расскажи про математику" in context
        assert "Текущий вопрос: А что дальше?" in context
    
    def test_history_limit(self):
        """Тест ограничения истории (только последние 5)"""
        user_message = "Вопрос"
        chat_history = []
        for i in range(10):  # 10 сообщений
            chat_history.extend([
                {"role": "user", "content": f"Вопрос {i}"},
                {"role": "ai", "content": f"Ответ {i}"}
            ])
        
        context = self.builder.build(user_message, chat_history)
        
        # Должны быть только последние 5 сообщений (5 строк, так как берутся последние 5 элементов из списка)
        history_lines = [line for line in context.split('\n') if 'user:' in line or 'ai:' in line]
        assert len(history_lines) == 5  # 5 последних сообщений
    
    def test_combined_context(self):
        """Тест комбинированного контекста"""
        user_message = "Спасибо!"
        chat_history = [
            {"role": "user", "content": "Помоги с задачей"},
            {"role": "ai", "content": "Конечно! Какую задачу?"}
        ]
        
        context = self.builder.build(user_message, chat_history, user_age=12)
        
        assert "ребенок 9-12 лет" in context
        assert "понятные примеры" in context
        assert "Предыдущие сообщения:" in context
        assert "user: Помоги с задачей" in context
        assert "ai: Конечно! Какую задачу?" in context
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
