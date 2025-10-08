"""
Построение контекста - единственная ответственность
Принцип Single Responsibility
"""

from typing import Dict, List, Optional
from bot.services.ai_response_generator_solid import IContextBuilder


class ContextBuilder(IContextBuilder):
    """Построение контекста - единственная ответственность"""
    
    def build(self, user_message: str, chat_history: List[Dict] = None, 
              user_age: Optional[int] = None) -> str:
        """Построение контекста для AI"""
        context_parts = []
        
        # Возрастная адаптация
        if user_age:
            age_context = self._get_age_context(user_age)
            context_parts.append(age_context)
        
        # История чата
        if chat_history:
            history_context = self._prepare_history_context(chat_history)
            context_parts.append(history_context)
        
        # Основное сообщение
        context_parts.append(f"Текущий вопрос: {user_message}")
        
        return "\n\n".join(context_parts)
    
    def _get_age_context(self, user_age: int) -> str:
        """Адаптация под возраст"""
        if user_age <= 8:
            return "Пользователь - ребенок 6-8 лет. Объясняй простыми словами."
        elif user_age <= 12:
            return "Пользователь - ребенок 9-12 лет. Используй понятные примеры."
        else:
            return "Пользователь - подросток 13-18 лет. Можно более сложные объяснения."
    
    def _prepare_history_context(self, chat_history: List[Dict]) -> str:
        """Подготовка истории чата"""
        history_text = "Предыдущие сообщения:\n"
        for msg in chat_history[-5:]:  # Только последние 5 сообщений
            history_text += f"{msg.get('role', 'user')}: {msg.get('content', '')}\n"
        return history_text
