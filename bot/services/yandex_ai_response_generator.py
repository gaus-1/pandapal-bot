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


def remove_duplicate_text(text: str, min_length: int = 20) -> str:
    """
    Удаляет повторяющиеся фрагменты текста (дубликаты).
    Агрессивная версия для полного удаления всех повторений.

    Args:
        text: Исходный текст
        min_length: Минимальная длина фрагмента для проверки на дубликат

    Returns:
        str: Текст без повторяющихся фрагментов
    """
    if not text or len(text) < min_length * 2:
        return text

    # Шаг 1: Проверяем, не повторяется ли весь текст целиком несколько раз
    text_len = len(text)
    if text_len > min_length * 3:
        # Разбиваем на 3 части и проверяем
        part_size = text_len // 3
        parts = [text[i : i + part_size] for i in range(0, text_len, part_size)]
        if len(parts) >= 2:
            normalized_parts = [re.sub(r"\s+", " ", p.lower().strip()) for p in parts[:3]]
            # Если все части одинаковые - оставляем только первую
            if len(normalized_parts) >= 2 and all(
                p == normalized_parts[0] for p in normalized_parts[1:] if len(p) >= min_length
            ):
                return parts[0].strip()

    # Шаг 2: Разбиваем на строки (по переносам)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    if len(lines) < 2:
        return text

    # Шаг 3: Удаляем дубликаты строк
    seen_lines = set()
    unique_lines = []

    for line in lines:
        # Нормализуем для сравнения
        normalized = re.sub(r"\s+", " ", line.lower().strip())

        # Проверяем дубликаты
        if len(normalized) >= min_length:
            if normalized not in seen_lines:
                seen_lines.add(normalized)
                unique_lines.append(line)
        else:
            # Короткие строки проверяем на точное совпадение
            if line not in unique_lines:
                unique_lines.append(line)

    result = "\n".join(unique_lines)

    # Шаг 4: Проверяем повторяющиеся блоки (несколько строк подряд)
    if len(unique_lines) >= 4:
        # Ищем блоки из 2-5 строк, которые повторяются
        seen_blocks = set()
        final_lines = []
        i = 0

        while i < len(unique_lines):
            # Проверяем блоки разной длины
            found_duplicate = False
            for block_len in range(5, 1, -1):  # От 5 до 2 строк
                if i + block_len > len(unique_lines):
                    continue

                block = "\n".join(unique_lines[i : i + block_len])
                normalized_block = re.sub(r"\s+", " ", block.lower().strip())

                if len(normalized_block) >= min_length * 2:
                    if normalized_block in seen_blocks:
                        # Пропускаем весь блок
                        i += block_len
                        found_duplicate = True
                        break
                    else:
                        seen_blocks.add(normalized_block)

            if not found_duplicate:
                final_lines.append(unique_lines[i])
                i += 1

        result = "\n".join(final_lines)

    # Шаг 5: Финальная проверка - удаляем повторяющиеся предложения
    sentences = re.split(r"([.!?]\s+)", result)
    if len(sentences) >= 4:
        seen_sentences = set()
        unique_sentences = []

        i = 0
        while i < len(sentences) - 1:
            sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
            normalized_sent = re.sub(r"\s+", " ", sentence.lower().strip())

            if len(normalized_sent) >= min_length:
                if normalized_sent not in seen_sentences:
                    seen_sentences.add(normalized_sent)
                    unique_sentences.append(sentence)
            else:
                unique_sentences.append(sentence)
            i += 2

        result = "".join(unique_sentences)

    return result.strip() if result.strip() else text.strip()


def clean_ai_response(text: str) -> str:
    """
    Очищает ответ AI от LaTeX, сложных математических символов и повторяющихся фрагментов.
    Сохраняет сравнения (>, <) и знаки препинания.
    Исправляет форматирование таблицы умножения.
    """
    if not text:
        return text

    # Сначала удаляем дубликаты (более агрессивно, минимальная длина 20)
    text = remove_duplicate_text(text, min_length=20)

    # Исправляем форматирование таблицы умножения
    # Паттерн 1: "1. 3 1 = 3" → "1. 3 × 1 = 3" (нумерованные списки - сначала обрабатываем их)
    text = re.sub(r"(\d+\.\s+)(\d+)\s+(\d+)\s*=\s*(\d+)", r"\1\2 × \3 = \4", text)
    # Паттерн 2: "3 1 = 3" → "3 × 1 = 3" (обычные выражения, но не если перед первым числом есть точка)
    text = re.sub(r"(?<!\d\.\s)(?<!\d\.)(\d+)\s+(\d+)\s*=\s*(\d+)", r"\1 × \2 = \3", text)
    # Паттерн 3: "3*3=9" → "3 × 3 = 9"
    text = re.sub(r"(\d+)\*(\d+)\s*=\s*(\d+)", r"\1 × \2 = \3", text)

    # Убираем знак доллара (ограничители формул в Telegram/Markdown)
    text = text.replace("$", "")

    # Убираем специфичные LaTeX команды (включая скобки)
    latex_patterns = [
        r"\\begin\{[^}]+\}.*?\\end\{[^}]+\}",  # Окружения (сначала сложные)
        r"\\frac\{[^}]+\}\{[^}]+\}",  # \frac{}{}
        r"\\sqrt\[[^\]]+\]\{[^}]+\}",  # \sqrt[n]{}
        r"\\sqrt\{[^}]+\}",  # \sqrt{}
        r"\\[a-zA-Z]+\{[^}]*\}",  # \command{}
        r"\\\[",  # \[
        r"\\\]",  # \]
        r"\\\{",  # \{
        r"\\\}",  # \}
        r"\\\(",  # \(
        r"\\\)",  # \)
        r"\\[a-zA-Z]+",  # \command (после всех других)
    ]
    for pattern in latex_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Убираем математические символы верхних индексов и спецзнаков
    # (Оставляем знаки препинания и базовые операторы + - =)
    complex_math_chars = [
        "²",
        "³",
        "∑",
        "∫",
        "∞",
        "∠",
        "°",
        "•",
        "×",
    ]  # × можно заменить на x, но лучше оставить
    for char in complex_math_chars:
        text = text.replace(char, "")

    # Очищаем лишние пробелы (но сохраняем абзацы - двойные переносы строк)
    text = re.sub(r"[ \t]+", " ", text)  # Множественные пробелы в одну строку
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # Множественные переносы строк в два
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
        skip_name_asking: bool = False,  # noqa: ARG002
        non_educational_questions_count: int = 0,
        is_premium: bool = False,  # noqa: ARG002
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
                user_message=user_message,
                user_name=user_name,
                chat_history=chat_history,
                is_history_cleared=is_history_cleared,
                message_count_since_name=message_count_since_name,
                non_educational_questions_count=non_educational_questions_count,
                user_age=user_age,
                is_auto_greeting_sent=False,  # Для обычных запросов всегда False
            )

            # Добавляем веб-контекст к промпту, если он есть
            if web_context:
                enhanced_system_prompt += f"\n\n📚 Дополнительная информация:\n{web_context}"

            # Используем Pro модель для всех пользователей (YandexGPT 5 Pro Latest - стабильная версия)
            # Формат yandexgpt/latest - как в примере из Yandex Cloud Console
            model_name = "yandexgpt/latest"
            temperature = settings.ai_temperature  # Основной параметр для всех пользователей
            max_tokens = settings.ai_max_tokens  # Основной параметр для всех пользователей

            # Генерация ответа через Yandex Cloud
            logger.info("📤 Отправка запроса в YandexGPT Pro...")
            response = await self.yandex_service.generate_text_response(
                user_message=user_message,  # Передаем чистое сообщение пользователя
                chat_history=yandex_history,
                system_prompt=enhanced_system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model_name,
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
