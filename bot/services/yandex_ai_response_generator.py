"""
Генератор ответов AI для Yandex Cloud (YandexGPT).

Использует Yandex Cloud AI сервисы (YandexGPT Lite, SpeechKit STT, Vision OCR).
Соблюдает архитектуру SOLID.
"""

import re
from abc import ABC, abstractmethod

from loguru import logger

from bot.config import settings
from bot.services.knowledge_service import get_knowledge_service
from bot.services.prompt_builder import get_prompt_builder

# Утилиты очистки вынесены в response_cleaner (SOLID: SRP — одна ответственность на модуль)
from bot.services.response_cleaner import (  # noqa: F401 — re-export для обратной совместимости
    _CLARIFICATION_MAX_MESSAGE_LEN,
    _CLARIFICATION_MIN_LAST_REPLY_LEN,
    _CLARIFICATION_PHRASES,
    _CLARIFICATION_RESPONSE,
    _FAREWELL_KEYWORDS,
    _ensure_paragraph_breaks,
    _merge_digit_only_lines,
    add_random_engagement_question,
    clean_ai_response,
    finalize_ai_response,
    fix_glued_words,
    normalize_bold_spacing,
    remove_duplicate_text,
)
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

    def _should_use_wikipedia(self, user_message: str) -> bool:
        """
        Определить, нужно ли использовать проверенные данные для этого вопроса.

        КРИТИЧЕСКИ ВАЖНО: Wikipedia должна использоваться для ВСЕХ образовательных вопросов!
        Исключения только для чисто вычислительных задач.

        Args:
            user_message: Сообщение пользователя.

        Returns:
            bool: True если стоит использовать проверенные данные.
        """
        message_lower = user_message.lower().strip()

        # Исключаем ТОЛЬКО чисто математические/вычислительные запросы
        # Для всех остальных используем Wikipedia!
        exclude_patterns = [
            r"^\d+\s*[\+\-\*\/×÷]\s*\d+",  # Чистые вычисления: "5 + 3", "7 × 8"
            r"^сколько будет\s+\d+",  # "Сколько будет 5+3"
            r"^реши\s+\d+",  # "Реши 5+3"
            r"^посчитай\s+\d+",  # "Посчитай 5+3"
            r"^вычисли\s+\d+",  # "Вычисли 5+3"
            r"покажи\s+таблицу\s+умножения",  # Таблица умножения - визуализация
            r"нарисуй\s+график",  # Графики - визуализация
            r"построй\s+график",  # Графики
            r"покажи\s+график",  # Графики
            r"привет",  # Приветствия
            r"^как\s+(?:тебя|твоя)\s+(?:зовут|имя)",  # Вопросы о боте
        ]

        # Для ВСЕХ остальных запросов используем Wikipedia (кроме исключений)
        # - "что такое фотосинтез" - да
        # - "кто такой Пушкин" - да
        # - "почему небо голубое" - да
        # - "какая столица Франции" - да
        # - "расскажи про ВОВ" - да
        # - "где находится Китай" - да
        # - "в каком году была война" - да
        # - любые образовательные вопросы - да!
        return all(not re.search(pattern, message_lower) for pattern in exclude_patterns)

    def _is_calculation_task(self, message: str) -> bool:
        """
        Определить, нужно ли использовать Zero-shot CoT (пошаговое рассуждение).
        Задачи с числами и многошаговой логикой — добавляем «Давайте решать пошагово».
        Исключаем нарративные упоминания слова «задача» без числовых вычислений.
        """
        ml = message.lower().strip()
        cot_triggers = [
            r"сколько\s+(всего|осталось|получилось|было|стало)",
            r"реши\s+(задачу|уравнение|пример)",
            r"вычисли|посчитай",
            r"\d+\s*[\+\-\*\/×÷]\s*\d+",  # Числа и операции
            r"было\s+\d+",  # «Было 23 яблока»
            r"купил[ио]?\s+\d+",
            r"ушло\s+\d+",
            r"осталось\s+\d+",
        ]
        # Слово «задача» триггерит CoT ТОЛЬКО если рядом есть числа
        if re.search(r"задач", ml) and re.search(r"\d", ml):
            return True
        return any(re.search(p, ml) for p in cot_triggers)

    @staticmethod
    def _should_ask_clarification(user_message: str, chat_history: list[dict] | None) -> bool:
        """
        True только при коротком неоднозначном продолжении: длина ≤25, в истории есть ответ
        assistant не короче 180 символов, сообщение входит в список продолжений.
        """
        msg = (user_message or "").strip()
        if len(msg) > _CLARIFICATION_MAX_MESSAGE_LEN:
            return False
        if not chat_history:
            return False
        last_assistant_text = None
        for m in reversed(chat_history):
            if m.get("role") == "assistant":
                last_assistant_text = (m.get("text") or "").strip()
                break
        if not last_assistant_text or len(last_assistant_text) < _CLARIFICATION_MIN_LAST_REPLY_LEN:
            return False
        return msg.lower() in _CLARIFICATION_PHRASES

    async def generate_response(
        self,
        user_message: str,
        chat_history: list[dict] = None,
        user_age: int | None = None,
        user_name: str | None = None,
        user_grade: int | None = None,
        is_history_cleared: bool = False,
        message_count_since_name: int = 0,
        skip_name_asking: bool = False,  # noqa: ARG002
        non_educational_questions_count: int = 0,
        is_premium: bool = False,
        is_auto_greeting_sent: bool = False,
        user_gender: str | None = None,
        emoji_in_chat: bool | None = None,
        history_message_limit: int | None = None,
    ) -> str:
        """
        Генерировать ответ AI на сообщение пользователя.

        Использует Pro модель для всех пользователей.
        Лимиты запросов управляются через premium_features_service.

        Args:
            user_message: Сообщение пользователя.
            chat_history: История предыдущих сообщений.
            user_age: Возраст пользователя для адаптации.
            user_name: Имя пользователя для обращения.
            is_history_cleared: Флаг очистки истории.
            message_count_since_name: Количество сообщений с последнего обращения по имени.
            skip_name_asking: Пропустить запрос имени (не используется в текущей реализации).
            non_educational_questions_count: Количество непредметных вопросов подряд.
            is_premium: Premium статус (не используется, оставлено для обратной совместимости)
            is_auto_greeting_sent: Флаг, что автоматическое приветствие уже было отправлено

        Returns:
            str: Сгенерированный ответ AI.
        """
        try:
            # Модерация: блокируем запрещённые темы до вызова API
            is_safe, block_reason = self.moderator.moderate(user_message)
            if not is_safe:
                from bot.services.moderation_service import ContentModerationService

                return ContentModerationService().get_safe_response_alternative(block_reason)

            if self._should_ask_clarification(user_message, chat_history):
                return _CLARIFICATION_RESPONSE

            if history_message_limit is None:
                history_message_limit = (
                    settings.chat_history_messages_for_api_premium
                    if is_premium
                    else settings.chat_history_messages_for_api_free
                )

            # RAG: запрос с учётом контекста диалога для коротких продолжений («а ещё?», «а почему?»)
            rag_query = self.knowledge_service.build_rag_query(user_message, chat_history)
            relevant_materials = await self.knowledge_service.enhanced_search(
                user_question=rag_query,
                user_age=user_age,
                top_k=3,
                use_wikipedia=self._should_use_wikipedia(user_message),
            )
            max_sent = (
                25
                if any(
                    w in user_message.lower()
                    for w in ("список", "таблица значений", "все значения")
                )
                else 15
            )
            web_context = self.knowledge_service.format_and_compress_knowledge_for_ai(
                relevant_materials, user_message, max_sentences=max_sent
            )

            # Преобразуем историю в формат Yandex Cloud (лимит задаётся вызывающей стороной)
            yandex_history = []
            if chat_history:
                for msg in chat_history[-history_message_limit:]:
                    role = msg.get("role", "user")
                    text = msg.get("text", "").strip()
                    if text:
                        yandex_history.append({"role": role, "text": text})

            # Используем PromptBuilder для формирования промпта
            prompt_builder = get_prompt_builder()
            # Если is_auto_greeting_sent не передан, проверяем историю
            if not is_auto_greeting_sent and chat_history:
                for msg in chat_history:
                    if msg.get("role") == "assistant":
                        msg_text = msg.get("text", "").lower()
                        if (
                            "привет" in msg_text
                            or "начнем" in msg_text
                            or "чем могу помочь" in msg_text
                        ):
                            is_auto_greeting_sent = True
                            break

            from bot.services.emoji_preference import compute_allow_emoji_this_turn

            allow_emoji_this_turn = compute_allow_emoji_this_turn(chat_history or [])
            enhanced_system_prompt = prompt_builder.build_system_prompt(
                user_message=user_message,
                user_name=user_name,
                chat_history=chat_history,
                is_history_cleared=is_history_cleared,
                message_count_since_name=message_count_since_name,
                non_educational_questions_count=non_educational_questions_count,
                user_age=user_age,
                user_grade=user_grade,
                is_auto_greeting_sent=is_auto_greeting_sent,
                user_gender=user_gender,
                emoji_in_chat=emoji_in_chat,
                allow_emoji_this_turn=allow_emoji_this_turn,
            )

            if web_context:
                from bot.config.prompts import RAG_FORMAT_REMINDER

                enhanced_system_prompt += (
                    f"\n\n📚 Дополнительная информация:\n{web_context}\n\n{RAG_FORMAT_REMINDER}\n\n"
                )
            from bot.config.prompts import STRUCTURE_REMINDER_ALWAYS

            enhanced_system_prompt += f"\n\n{STRUCTURE_REMINDER_ALWAYS}\n\n"

            # Используем Pro модель для всех пользователей (YandexGPT Pro Latest - стабильная версия)
            # Формат yandexgpt-pro/latest - Pro версия YandexGPT
            model_name = settings.yandex_gpt_model
            temperature = settings.ai_temperature  # Основной параметр для всех пользователей
            max_tokens = settings.ai_max_tokens  # Основной параметр для всех пользователей

            # Zero-shot CoT: для задач с вычислениями добавляем триггер пошагового рассуждения
            message_for_api = user_message
            if self._is_calculation_task(user_message):
                message_for_api = f"{user_message.rstrip()} Давайте решать пошагово."
                logger.debug("CoT: добавлен триггер пошагового рассуждения")

            # Генерация ответа через Yandex Cloud
            logger.info("📤 Отправка запроса в YandexGPT Pro...")
            response = await self.yandex_service.generate_text_response(
                user_message=message_for_api,
                chat_history=yandex_history,
                system_prompt=enhanced_system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model_name,
            )

            if response:
                return finalize_ai_response(response, user_message=user_message)
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
                # Очищаем ответ от дубликатов и форматируем
                cleaned_analysis = clean_ai_response(analysis_result["analysis"])
                response_parts.append(f"🎓 <b>Разбор задания:</b>\n{cleaned_analysis}")

            result = "\n".join(response_parts)
            return finalize_ai_response(result, user_message=user_message or "")

        except Exception as e:
            logger.error(f"❌ Ошибка анализа изображения (Yandex): {e}")
            return "😔 Извини, у меня возникли проблемы с анализом изображения. Попробуй ещё раз!"

    async def moderate_image_content(self, image_data: bytes) -> tuple[bool, str]:
        """
        Проверить изображение на безопасность.

        Базовая проверка: если OCR распознал текст, прогоняем его через модерацию.
        Это защищает от пересылки изображений с запрещённым текстовым контентом.

        Args:
            image_data: Данные изображения в байтах.

        Returns:
            tuple[bool, str]: (is_safe, reason)
        """
        try:
            ocr_result = await self.yandex_service.recognize_text(image_data)
            if ocr_result and ocr_result.strip():
                is_safe, reason = self.moderator.moderate(ocr_result)
                if not is_safe:
                    logger.warning(f"⚠️ Изображение заблокировано модерацией: {reason}")
                    return False, reason
        except Exception as e:
            # OCR недоступен — пропускаем, не блокируем
            logger.debug(f"Модерация изображения: OCR недоступен ({e})")
        return True, "OK"
