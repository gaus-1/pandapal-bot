"""
Построитель контекста для генерации ответов AI.

Этот модуль реализует логику построения контекста для передачи в AI модель,
включая адаптацию под возраст пользователя и формирование истории чата.
Следует принципу Single Responsibility - единственная задача: построение контекста.
"""

from typing import Dict, List, Optional

from bot.services.ai_response_generator_solid import IContextBuilder


class ContextBuilder(IContextBuilder):
    """
    Построитель контекста для AI с адаптацией под возраст пользователя.

    Единственная ответственность: формирование контекста для передачи в AI модель
    с учетом возраста пользователя и истории предыдущих сообщений.
    """

    def build(
        self, user_message: str, chat_history: List[Dict] = None, user_age: Optional[int] = None
    ) -> str:
        """
        Построить контекст для генерации ответа AI.

        Формирует структурированный контекст, включающий адаптацию под возраст
        пользователя и историю предыдущих сообщений для поддержания диалога.

        Args:
            user_message (str): Текущее сообщение пользователя.
            chat_history (List[Dict], optional): История предыдущих сообщений.
            user_age (Optional[int]): Возраст пользователя для адаптации ответа.

        Returns:
            str: Сформированный контекст для передачи в AI модель.
        """
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
        """
        Получить контекст адаптации под возраст пользователя.

        Args:
            user_age (int): Возраст пользователя.

        Returns:
            str: Инструкция для AI по адаптации ответа под возраст.
        """
        if user_age <= 8:
            return "Пользователь - ребенок 6-8 лет. Объясняй простыми словами."
        elif user_age <= 12:
            return "Пользователь - ребенок 9-12 лет. Используй понятные примеры."
        else:
            return "Пользователь - подросток 13-18 лет. Можно более сложные объяснения."

    def _prepare_history_context(self, chat_history: List[Dict]) -> str:
        """
        Подготовить контекст из истории чата.

        Формирует текстовое представление последних сообщений для поддержания
        контекста диалога. Поддерживает разные форматы сообщений (content/parts).

        Args:
            chat_history (List[Dict]): История сообщений чата.

        Returns:
            str: Отформатированная история последних сообщений.
        """
        history_text = "Предыдущие сообщения:\n"
        for msg in chat_history[-5:]:  # Только последние 5 сообщений
            # Поддерживаем оба формата: 'content' и 'parts'
            content = msg.get("content", "")
            if not content and "parts" in msg:
                content = msg["parts"][0] if isinstance(msg["parts"], list) and msg["parts"] else ""

            role = msg.get("role", "user")
            role_text = "Пользователь" if role == "user" else "AI"
            history_text += f"{role_text}: {content}\n"
        return history_text
