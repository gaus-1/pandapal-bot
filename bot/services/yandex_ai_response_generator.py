"""
Генератор ответов AI для Yandex Cloud (YandexGPT).

Использует Yandex Cloud AI сервисы (YandexGPT Lite, SpeechKit STT, Vision OCR).
Соблюдает архитектуру SOLID.
"""

import asyncio
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

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
    def moderate(self, text: str) -> Tuple[bool, str]:
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
        self,
        user_message: str,
        chat_history: List[Dict] = None,
        user_age: Optional[int] = None,
        user_name: Optional[str] = None,
        is_history_cleared: bool = False,
        message_count_since_name: int = 0,
        skip_name_asking: bool = False,
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
                # Мягко переводим на учебу, НЕ повторяем запрещенную тему
                friendly_responses = [
                    "Привет! Давай лучше поговорим об учёбе! 📚 Чем могу помочь?",
                    "Ой, давай лучше обсудим что-то интересное из школы! ✨ Какой предмет тебе нравится?",
                    "Хм, давай лучше поговорим о чём-то полезном для учёбы! 🎓 Есть вопросы по урокам?",
                    "Давай лучше обсудим что-то интересное! 📖 Какой предмет изучаем сегодня?",
                    "О, а давай поговорим об учёбе! 🐼 Есть вопросы по школьным предметам?",
                ]
                return random.choice(friendly_responses)

            # Получение релевантных материалов из веб-источников
            relevant_materials = await self.knowledge_service.get_helpful_content(
                user_message, user_age
            )
            web_context = self.knowledge_service.format_knowledge_for_ai(relevant_materials)

            # Преобразуем историю в формат Yandex Cloud
            yandex_history = []
            if chat_history:
                for msg in chat_history[-10:]:  # Последние 10 сообщений
                    role = msg.get("role", "user")  # Используем роль напрямую из истории
                    text = msg.get("text", "").strip()
                    if text:  # Только непустые сообщения
                        yandex_history.append({"role": role, "text": text})

            # Формируем system_prompt с учетом возраста, имени и веб-контекста
            enhanced_system_prompt = AI_SYSTEM_PROMPT

            if user_age:
                enhanced_system_prompt += (
                    f"\n\nВажно: Адаптируй ответ под возраст пользователя ({user_age} лет)."
                )

            # Логика обращения по имени (1 раз в 5-10 сообщений пользователя)
            # Считаем что если прошло 5-10 сообщений, можно обратиться по имени
            if user_name and message_count_since_name >= 5:
                # Обращаемся по имени если прошло 7-10 сообщений, или случайно при 5-6
                if message_count_since_name >= 7 or (
                    message_count_since_name >= 5 and random.random() < 0.3
                ):
                    enhanced_system_prompt += (
                        f"\n\nВАЖНО: Обратись к пользователю по имени '{user_name}' в начале ответа. "
                        f"Используй имя естественно, например: '{user_name}, давай разберём это!' или "
                        f"'Понял, {user_name}! Сейчас объясню...' "
                        f"Не злоупотребляй - обращайся по имени только иногда, не в каждом ответе!"
                    )

            # Если история очищена - уточнить имя (только если пользователь не отказался)
            if is_history_cleared and not user_name and not skip_name_asking:
                enhanced_system_prompt += (
                    "\n\nВАЖНО: История чата была очищена. "
                    "В начале ответа ПОПРОСИ пользователя назвать своё имя, "
                    "чтобы ты мог обращаться к нему по имени в будущем. "
                    "Например: 'Привет! Давай знакомиться! Как тебя зовут? 🐼'\n\n"
                    "Если пользователь отказывается называть имя (пишет 'не хочу', 'не скажу', 'не буду' и т.д.), "
                    "вежливо скажи что это нормально и больше не спрашивай об имени. "
                    "Если пользователь написал что-то что НЕ похоже на имя (обычные слова, фразы, ерунду), "
                    "вежливо уточни: 'Хм, это не очень похоже на имя. Можешь назвать своё настоящее имя? "
                    "Например: Саша, Маша, Данил и т.д. Если не хочешь - скажи, и я больше не буду спрашивать! 😊'"
                )

            if web_context:
                enhanced_system_prompt += f"\n\nДополнительная информация:\n{web_context}"

            # Генерация ответа через Yandex Cloud
            logger.info("📤 Отправка запроса в YandexGPT...")
            response = await self.yandex_service.generate_text_response(
                user_message=user_message,  # Передаем чистое сообщение пользователя
                chat_history=yandex_history,
                system_prompt=enhanced_system_prompt,
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

    async def moderate_image_content(self, image_data: bytes) -> Tuple[bool, str]:
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
