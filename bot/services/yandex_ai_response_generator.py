"""
Генератор ответов AI для Yandex Cloud (YandexGPT).

Миграция с Google Gemini на Yandex Cloud.
Сохраняет архитектуру SOLID.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from loguru import logger

from bot.config import AI_SYSTEM_PROMPT, settings
from bot.services.knowledge_service import get_knowledge_service
from bot.services.yandex_cloud_service import get_yandex_cloud_service


class IModerator(ABC):
    """
    Интерфейс для модерации контента.

    Следует принципу Interface Segregation (ISP).
    """

    @abstractmethod
    def moderate(self, text: str) -> tuple[bool, str]:
        """
        Проверить текст на соответствие правилам модерации.

        Args:
            text: Текст для проверки.

        Returns:
            tuple[bool, str]: (is_safe, reason)
        """
        pass


class IContextBuilder(ABC):
    """
    Интерфейс для построения контекста для AI.

    Следует принципу Interface Segregation (ISP).
    """

    @abstractmethod
    def build(
        self, user_message: str, chat_history: List[Dict] = None, user_age: Optional[int] = None
    ) -> str:
        """
        Построить контекст для генерации ответа AI.

        Args:
            user_message: Текущее сообщение пользователя.
            chat_history: История предыдущих сообщений.
            user_age: Возраст пользователя для адаптации ответа.

        Returns:
            str: Сформированный контекст для AI модели.
        """
        pass


class YandexAIResponseGenerator:
    """
    Генератор ответов AI через Yandex Cloud (YandexGPT).

    Единственная ответственность - генерация ответов AI.
    Модерация и контекст делегируются через Dependency Injection (SOLID).
    """

    def __init__(self, moderator: IModerator, context_builder: IContextBuilder):
        """
        Инициализация генератора ответов.

        Args:
            moderator: Сервис модерации контента.
            context_builder: Сервис построения контекста.
        """
        self.moderator = moderator
        self.context_builder = context_builder
        self.knowledge_service = get_knowledge_service()

        # Инициализация Yandex Cloud сервиса
        self.yandex_service = get_yandex_cloud_service()

        logger.info("✅ Yandex AI Response Generator инициализирован")

    async def generate_response(
        self, user_message: str, chat_history: List[Dict] = None, user_age: Optional[int] = None
    ) -> str:
        """
        Генерировать ответ AI на сообщение пользователя.

        Args:
            user_message: Сообщение пользователя.
            chat_history: История предыдущих сообщений.
            user_age: Возраст пользователя для адаптации.

        Returns:
            str: Сгенерированный ответ AI.
        """
        try:
            # Модерация контента (делегирование)
            is_safe, reason = self.moderator.moderate(user_message)
            if not is_safe:
                return f"Извините, но я не могу обсуждать эту тему. {reason}"

            # Получение релевантных материалов из веб-источников
            relevant_materials = await self.knowledge_service.get_helpful_content(
                user_message, user_age
            )
            web_context = self.knowledge_service.format_knowledge_for_ai(relevant_materials)

            # Построение контекста (делегирование)
            context = self.context_builder.build(user_message, chat_history, user_age)

            # Добавляем веб-контекст
            if web_context:
                context += "\n\n" + web_context

            # Преобразуем историю в формат Yandex Cloud
            yandex_history = []
            if chat_history:
                for msg in chat_history[-10:]:  # Последние 10 сообщений
                    role = "user" if msg.get("is_user") else "assistant"
                    yandex_history.append({"role": role, "text": msg.get("text", "")})

            # Генерация ответа через Yandex Cloud
            logger.info("📤 Отправка запроса в YandexGPT...")
            response = await self.yandex_service.generate_text_response(
                user_message=context,
                chat_history=yandex_history,
                system_prompt=AI_SYSTEM_PROMPT,
                temperature=settings.ai_temperature,
                max_tokens=settings.ai_max_tokens,
            )

            if response:
                return response.strip()
            else:
                return "Извините, не смог сгенерировать ответ. Попробуйте переформулировать вопрос."

        except Exception as e:
            logger.error(f"❌ Ошибка генерации AI (Yandex): {e}")
            return "Ой, что-то пошло не так. Попробуйте переформулировать вопрос."

    def get_model_info(self) -> Dict[str, str]:
        """
        Получить информацию о текущей модели AI.

        Returns:
            Dict[str, str]: Информация о модели Yandex Cloud.
        """
        return {
            "provider": "Yandex Cloud",
            "model": settings.yandex_gpt_model,
            "temperature": str(settings.ai_temperature),
            "max_tokens": str(settings.ai_max_tokens),
            "public_name": "PandaPalAI (powered by YandexGPT)",
        }

    async def analyze_image(
        self, image_data: bytes, user_message: Optional[str] = None, user_age: Optional[int] = None
    ) -> str:
        """
        Анализировать изображение через Yandex Vision + YandexGPT.

        Args:
            image_data: Данные изображения в байтах.
            user_message: Сопровождающий текст пользователя.
            user_age: Возраст пользователя для адаптации.

        Returns:
            str: Образовательный ответ на основе анализа изображения.
        """
        try:
            logger.info("📷 Анализ изображения через Yandex Vision + GPT...")

            # Анализируем изображение через Yandex Vision + GPT
            analysis_result = await self.yandex_service.analyze_image_with_text(
                image_data=image_data, user_question=user_message
            )

            if not analysis_result.get("has_text") and not analysis_result.get("analysis"):
                return (
                    "📷 Я не смог распознать текст на изображении.\n\n"
                    "Попробуй сфотографировать задание более четко! 📝"
                )

            # Формируем образовательный ответ
            response_parts = []

            if analysis_result.get("recognized_text"):
                response_parts.append(
                    f"📝 <b>Текст на изображении:</b>\n{analysis_result['recognized_text']}\n"
                )

            if analysis_result.get("analysis"):
                response_parts.append(f"🎓 <b>Разбор задания:</b>\n{analysis_result['analysis']}")

            return "\n".join(response_parts)

        except Exception as e:
            logger.error(f"❌ Ошибка анализа изображения (Yandex): {e}")
            return "😔 Извини, у меня возникли проблемы с анализом изображения. Попробуй ещё раз!"

    async def moderate_image_content(self, image_data: bytes) -> tuple[bool, str]:
        """
        Проверить изображение на безопасность.

        Args:
            image_data: Данные изображения в байтах.

        Returns:
            tuple[bool, str]: (is_safe, reason)
        """
        try:
            # Yandex Vision для базовой проверки
            analysis_result = await self.yandex_service.analyze_image_with_text(image_data)

            # Проверяем текст на запрещенные темы
            if analysis_result.get("recognized_text"):
                is_safe, reason = self.moderator.moderate(analysis_result["recognized_text"])
                if not is_safe:
                    return False, f"Небезопасное содержание: {reason}"

            return True, "Изображение безопасно"

        except Exception as e:
            logger.error(f"❌ Ошибка модерации изображения: {e}")
            return False, "Ошибка анализа изображения"
