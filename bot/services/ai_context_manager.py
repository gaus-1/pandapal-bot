"""
Менеджер контекста AI - отвечает только за управление контекстом и историей
Соблюдает принцип Single Responsibility Principle
"""

from typing import Dict, List, Optional
from loguru import logger


class AIContextManager:
    """Менеджер контекста AI - только управление историей и контекстом"""

    def __init__(self):
        """Инициализация менеджера контекста"""
        self.max_history_length = 10  # Максимум сообщений для контекста

    def prepare_context(
        self,
        user_message: str,
        chat_history: List[Dict[str, str]] = None,
        user_age: Optional[int] = None,
        user_grade: Optional[int] = None,
    ) -> str:
        """Подготовка контекста для AI"""

        # Адаптация под возраст
        age_context = self._get_age_context(user_age, user_grade)

        # Подготовка истории
        history_context = self._prepare_history_context(chat_history)

        # Формирование полного контекста
        full_context = f"{age_context}\n{history_context}\nUser: {user_message}\nAssistant:"

        return full_context

    def _get_age_context(self, user_age: Optional[int], user_grade: Optional[int]) -> str:
        """Получение контекста возраста"""
        if user_age:
            if user_age <= 7:
                return (
                    "Отвечай как для ребенка 4-7 лет: простыми словами, с примерами из мультиков."
                )
            elif user_age <= 12:
                return "Отвечай как для ребенка 8-12 лет: доступно, но уже более подробно."
            elif user_age <= 16:
                return "Отвечай как для подростка 13-16 лет: более сложно, но понятно."
            else:
                return "Отвечай как для взрослого: подробно и развернуто."

        if user_grade:
            if user_grade <= 4:
                return "Отвечай как для начальной школы: просто и наглядно."
            elif user_grade <= 9:
                return "Отвечай как для средней школы: подробно и с примерами."
            else:
                return "Отвечай как для старшей школы: углубленно и академично."

        return "Отвечай дружелюбно и понятно для школьника."

    def _prepare_history_context(self, chat_history: List[Dict[str, str]] = None) -> str:
        """Подготовка контекста истории"""
        if not chat_history:
            return ""

        # Берем последние сообщения
        recent_history = chat_history[-self.max_history_length :]

        # Форматируем историю
        history_lines = []
        for msg in recent_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_lines.append(f"{role}: {content}")

        return "\n".join(history_lines)

    def extract_keywords(self, message: str) -> List[str]:
        """Извлечение ключевых слов из сообщения"""
        # Простое извлечение ключевых слов
        words = message.lower().split()

        # Фильтруем стоп-слова
        stop_words = {"и", "в", "на", "с", "по", "для", "от", "до", "как", "что", "где", "когда"}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        return keywords[:5]  # Максимум 5 ключевых слов

    def is_question(self, message: str) -> bool:
        """Проверка, является ли сообщение вопросом"""
        question_indicators = ["?", "что", "как", "где", "когда", "почему", "зачем", "который"]
        message_lower = message.lower()

        return any(indicator in message_lower for indicator in question_indicators)
