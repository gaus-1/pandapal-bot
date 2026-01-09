"""
Генератор ответов AI для Yandex Cloud (YandexGPT).

Использует Yandex Cloud AI сервисы (YandexGPT Lite, SpeechKit STT, Vision OCR).
Соблюдает архитектуру SOLID.
"""

import random
import re
from abc import ABC, abstractmethod

from loguru import logger

from bot.config import settings
from bot.services.knowledge_service import get_knowledge_service
from bot.services.prompt_builder import get_prompt_builder
from bot.services.yandex_cloud_service import get_yandex_cloud_service


def clean_ai_response(text: str) -> str:
    """
    Очистить ответ AI от запрещенных символов и LaTeX.

    Удаляет:
    - Символы $ (доллар)
    - LaTeX команды (\\frac, \\sqrt, \\text, \\cdot, ^, _, \\begin, \\end, \\[, \\], \\(, \\))
    - Сложные математические символы (², ³, ∑, ∫, ∞, ≈, ≤, ≥, ∠, °)

    Args:
        text: Текст ответа AI.

    Returns:
        str: Очищенный текст.
    """
    if not text:
        return text

    # Удаляем символы доллара (все вхождения)
    text = text.replace("$", "")

    # Удаляем LaTeX команды (в правильном порядке - сначала сложные, потом простые)
    latex_patterns = [
        r"\\frac\{[^}]+\}\{[^}]+\}",  # \frac{}{}
        r"\\sqrt\[[^\]]+\]\{[^}]+\}",  # \sqrt[n]{}
        r"\\sqrt\{[^}]+\}",  # \sqrt{}
        r"\\text\{[^}]+\}",  # \text{}
        r"\\begin\{[^}]+\}.*?\\end\{[^}]+\}",  # \begin{}...\end{} (многострочные)
        r"\\begin\{[^}]+\}",  # \begin{}
        r"\\end\{[^}]+\}",  # \end{}
        r"\\cdot",  # \cdot
        r"\\\[",  # \[
        r"\\\]",  # \]
        r"\\\(",  # \(
        r"\\\)",  # \)
        r"\\[a-zA-Z]+\{[^}]*\}",  # Любые другие LaTeX команды с {}
        r"\\[a-zA-Z]+",  # Любые другие LaTeX команды
    ]

    for pattern in latex_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Удаляем оставшиеся обратные слэши перед буквами (LaTeX команды без скобок)
    text = re.sub(r"\\[a-zA-Z]", "", text)

    # Удаляем сложные математические символы
    math_symbols = ["²", "³", "∑", "∫", "∞", "≈", "≤", "≥", "∠", "°"]
    for symbol in math_symbols:
        text = text.replace(symbol, "")

    # Удаляем множественные пробелы
    text = re.sub(r"\s+", " ", text)

    # Удаляем пробелы в начале и конце
    text = text.strip()

    return text


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
        self, user_message: str, chat_history: list[dict] = None, user_age: int | None = None
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

    def __init__(
        self,
        moderator: IModerator,
        context_builder: IContextBuilder,
        knowledge_service=None,  # type: ignore
        yandex_service=None,  # type: ignore
    ):
        """
        Инициализация генератора ответов.

        Args:
            moderator: Сервис модерации контента.
            context_builder: Сервис построения контекста.
            knowledge_service: Опционально - сервис знаний (для DI).
                Если None, используется глобальный синглтон.
            yandex_service: Опционально - Yandex Cloud сервис (для DI).
                Если None, используется глобальный синглтон.
        """
        self.moderator = moderator
        self.context_builder = context_builder

        # Dependency Injection: используем переданные сервисы или глобальные синглтоны
        # Это позволяет тестировать с моками и улучшает соблюдение DIP
        self.knowledge_service = (
            knowledge_service if knowledge_service is not None else get_knowledge_service()
        )
        self.yandex_service = (
            yandex_service if yandex_service is not None else get_yandex_cloud_service()
        )

        logger.info("✅ Yandex AI Response Generator инициализирован")

    async def generate_response(
        self,
        user_message: str,
        chat_history: list[dict] = None,
        user_age: int | None = None,
        user_name: str | None = None,
        is_history_cleared: bool = False,
        message_count_since_name: int = 0,
        non_educational_questions_count: int = 0,  # noqa: ARG002
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

            # Используем PromptBuilder для формирования промпта
            prompt_builder = get_prompt_builder()
            enhanced_system_prompt = prompt_builder.build_system_prompt(
                user_age=user_age,
                user_name=user_name,
                user_message_count=message_count_since_name,
                is_history_cleared=is_history_cleared,
                history=chat_history,
                user_message=user_message,
                web_context=web_context,
                non_educational_count=non_educational_questions_count,
            )

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
                # Очищаем ответ от запрещенных символов и LaTeX
                cleaned_response = clean_ai_response(response.strip())
                return cleaned_response
            else:
                return "Извините, не смог сгенерировать ответ. Попробуйте переформулировать вопрос."

        except Exception as e:
            logger.error(f"❌ Ошибка генерации AI (Yandex): {e}")
            return "Ой, что-то пошло не так. Попробуйте переформулировать вопрос."

    def get_model_info(self) -> dict[str, str]:
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
        self,
        image_data: bytes,
        user_message: str | None = None,
        user_age: int | None = None,  # noqa: ARG002
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
