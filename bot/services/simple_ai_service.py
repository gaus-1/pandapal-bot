"""
Упрощенный AI сервис для генерации ответов PandaPalAI.

Этот модуль реализует упрощенную версию AI сервиса, объединяя все функции
в одном классе без избыточных абстракций. Предоставляет полный функционал
для генерации ответов AI с модерацией и адаптацией под возраст пользователя.

Основные возможности:
- Генерация ответов через Google Gemini AI
- Базовая модерация контента
- Адаптация ответов под возраст пользователя
- Обработка истории чата для контекста
- Безопасные настройки генерации

Архитектура:
- Упрощенная структура без сложных абстракций
- Все функции в одном классе для простоты
- Прямое использование Google Generative AI
- Встроенная модерация контента

Использование:
- Для простых случаев без сложной логики
- Когда не нужны продвинутые возможности SOLID архитектуры
- Для быстрой разработки и прототипирования
"""

from typing import Dict, List, Optional

import google.generativeai as genai
from loguru import logger

from bot.config import AI_SYSTEM_PROMPT, FORBIDDEN_PATTERNS, settings


class SimpleAIService:
    """
    Упрощенный AI сервис для генерации ответов PandaPalAI.

    Объединяет все функции AI сервиса в одном классе для простоты
    использования. Включает в себя генерацию ответов, модерацию контента
    и адаптацию под возраст пользователя.
    """

    def __init__(self):
        """
        Инициализация упрощенного AI сервиса.

        Настраивает Google Gemini AI с безопасными параметрами генерации
        и настройками безопасности для работы с детьми.
        """
        genai.configure(api_key=settings.gemini_api_key)

        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": settings.ai_temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": settings.ai_max_tokens,
            },
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
            ],
            system_instruction=AI_SYSTEM_PROMPT,
        )

        logger.info(f"✅ Simple AI Service инициализирован: {settings.gemini_model}")

    def moderate_content(self, text: str) -> tuple[bool, str]:
        """Простая модерация по ключевым словам"""
        text_lower = text.lower()

        for pattern in FORBIDDEN_PATTERNS:
            if pattern.lower() in text_lower:
                return False, f"Запрещенная тема: {pattern}"

        return True, "Контент безопасен"

    def prepare_context(
        self, user_message: str, chat_history: List[Dict] = None, user_age: Optional[int] = None
    ) -> str:
        """Подготовка контекста для AI"""
        context_parts = []

        # Возрастная адаптация
        if user_age:
            if user_age <= 8:
                context_parts.append("Пользователь - ребенок 6-8 лет. Объясняй простыми словами.")
            elif user_age <= 12:
                context_parts.append("Пользователь - ребенок 9-12 лет. Используй понятные примеры.")
            else:
                context_parts.append(
                    "Пользователь - подросток 13-18 лет. Можно более сложные объяснения."
                )

        # История чата
        if chat_history:
            history_text = "Предыдущие сообщения:\n"
            for msg in chat_history[-5:]:  # Только последние 5 сообщений
                history_text += f"{msg.get('role', 'user')}: {msg.get('content', '')}\n"
            context_parts.append(history_text)

        # Основное сообщение
        context_parts.append(f"Текущий вопрос: {user_message}")

        return "\n\n".join(context_parts)

    async def generate_response(
        self, user_message: str, chat_history: List[Dict] = None, user_age: Optional[int] = None
    ) -> str:
        """Генерация ответа AI"""
        try:
            # Модерация контента
            is_safe, reason = self.moderate_content(user_message)
            if not is_safe:
                return f"Извините, но я не могу обсуждать эту тему. {reason}"

            # Подготовка контекста
            context = self.prepare_context(user_message, chat_history, user_age)

            # Генерация ответа
            response = await self.model.generate_content_async(context)

            if response and response.text:
                return response.text.strip()
            else:
                return "Извините, не смог сгенерировать ответ. Попробуйте переформулировать вопрос."

        except Exception as e:
            logger.error(f"❌ Ошибка генерации AI: {e}")
            return "Ой, что-то пошло не так. Попробуйте переформулировать вопрос."

    def get_model_info(self) -> Dict[str, str]:
        """Информация о модели"""
        return {
            "model": settings.gemini_model,
            "temperature": str(settings.ai_temperature),
            "max_tokens": str(settings.ai_max_tokens),
            "public_name": "PandaPalAI",
        }


# Глобальный экземпляр
_simple_ai_service = None


def get_simple_ai_service() -> SimpleAIService:
    """
    Получить глобальный экземпляр упрощенного AI сервиса.

    Реализует паттерн Singleton для обеспечения единого экземпляра
    упрощенного AI сервиса во всем приложении.

    Returns:
        SimpleAIService: Глобальный экземпляр упрощенного AI сервиса.
    """
    global _simple_ai_service
    if _simple_ai_service is None:
        _simple_ai_service = SimpleAIService()
    return _simple_ai_service
