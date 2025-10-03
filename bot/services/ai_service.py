"""
Сервис для работы с Google Gemini AI
Обеспечивает общение с ИИ, адаптацию под возраст, память контекста
Поддерживает обработку изображений через Gemini Vision API
@module bot.services.ai_service
"""

import base64
import hashlib
import io
from typing import Dict, List, Optional, Union

import google.generativeai as genai
from loguru import logger
from PIL import Image

from bot.config import AI_SYSTEM_PROMPT, settings
from bot.services.cache_service import AIResponseCache, UserCache, cache_service
from bot.services.moderation_service import ContentModerationService


class GeminiAIService:
    """
    Сервис для работы с Google Gemini AI

    Возможности:
    - Генерация текстовых ответов с учётом контекста (50 последних сообщений)
    - Адаптация под возраст ребёнка
    - Модерация контента (входящего и исходящего)
    - Генерация решений задач, объяснений, примеров
    - Обработка изображений через Gemini Vision API
    - Анализ фото для образовательных целей
    - Модерация изображений для безопасности детей
    """

    def __init__(self):
        """
        Инициализация Gemini AI
        Настройка API ключа и модели
        """
        # Конфигурация Gemini API
        genai.configure(api_key=settings.gemini_api_key)

        # Настройки генерации
        self.generation_config = {
            "temperature": settings.ai_temperature,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": settings.ai_max_tokens,
        }

        # Настройки безопасности Gemini (блокировка опасного контента)
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",  # Блокируем harassment
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",  # Блокируем hate speech
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",  # Блокируем 18+ контент
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",  # Блокируем опасный контент
            },
        ]

        # Инициализация модели
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
            system_instruction=AI_SYSTEM_PROMPT,  # Системный промпт PandaPalAI
        )

        # Сервис модерации
        self.moderation = ContentModerationService()

        logger.info(f"✅ Gemini AI инициализирован: модель {settings.gemini_model}")

    async def generate_response(
        self,
        user_message: str,
        chat_history: List[Dict[str, str]] = None,
        user_age: Optional[int] = None,
        user_grade: Optional[int] = None,
    ) -> str:
        """
        Генерация ответа AI с учётом контекста и возраста

        Args:
            user_message: Сообщение от пользователя
            chat_history: История чата (последние 50 сообщений)
            user_age: Возраст ребёнка (для адаптации языка)
            user_grade: Класс (для адаптации сложности)

        Returns:
            str: Ответ от AI

        Raises:
            ValueError: Если контент заблокирован модерацией
        """
        try:
            # Проверяем кэш ответов AI
            query_hash = hashlib.md5(f"{user_message}:{user_age}:{user_grade}".encode()).hexdigest()
            cached_response = await AIResponseCache.get_response(query_hash)

            if cached_response:
                logger.debug(f"💾 AI ответ получен из кэша для запроса: {user_message[:50]}...")
                return cached_response

            # ШАГ 1: Модерация входящего сообщения
            is_safe, reason = self.moderation.is_safe_content(user_message)

            if not is_safe:
                logger.warning(f"🚫 Заблокировано сообщение: {reason}")
                self.moderation.log_blocked_content(0, user_message, reason)

                # Возвращаем дружелюбный отказ
                return self.moderation.get_safe_response_alternative(reason)

            # ШАГ 2: Подготовка контекста (возраст и класс)
            context_instruction = self._build_context_instruction(user_age, user_grade)

            # ШАГ 3: Формирование промпта с контекстом
            full_message = f"{context_instruction}\n\nВопрос ребёнка: {user_message}"

            # ШАГ 4: Создание чата с историей
            if chat_history:
                # Используем историю для контекста
                chat = self.model.start_chat(history=chat_history)
                response = chat.send_message(full_message)
            else:
                # Первое сообщение без истории
                response = self.model.generate_content(full_message)

            # Извлекаем текст ответа
            ai_response = response.text

            # ШАГ 5: Модерация ответа AI (дополнительная проверка)
            ai_response = self.moderation.sanitize_ai_response(ai_response)

            # Сохраняем ответ в кэш
            await AIResponseCache.set_response(query_hash, ai_response, ttl=1800)  # 30 минут

            logger.info(f"🤖 AI ответил (длина: {len(ai_response)} символов)")

            return ai_response

        except Exception as e:
            logger.error(f"❌ Ошибка генерации AI: {e}")

            # Безопасный fallback ответ при ошибке
            return (
                "Ой, кажется у меня технические проблемы 🔧 "
                "Попробуй спросить чуть позже или перефразируй вопрос!"
            )

    def _build_context_instruction(self, age: Optional[int], grade: Optional[int]) -> str:
        """
        Построение инструкции с учётом возраста и класса
        Адаптирует сложность и стиль ответа

        Args:
            age: Возраст ребёнка
            grade: Класс

        Returns:
            str: Дополнительная инструкция для AI
        """
        context_parts = []

        if age:
            if age <= 10:
                context_parts.append(
                    "Ребёнку 6-10 лет. Используй ОЧЕНЬ простой язык, "
                    "короткие предложения, много примеров из повседневной жизни."
                )
            elif age <= 13:
                context_parts.append(
                    "Ребёнку 11-13 лет. Используй понятный язык, "
                    "можно чуть более сложные термины, но объясняй их."
                )
            else:
                context_parts.append(
                    "Подростку 14-18 лет. Можешь использовать более "
                    "академический язык, но оставайся дружелюбным."
                )

        if grade:
            context_parts.append(
                f"Ученик {grade} класса. Ориентируйся на программу {grade} класса."
            )

        if context_parts:
            return "КОНТЕКСТ: " + " ".join(context_parts)

        return ""

    async def explain_topic(self, topic: str, subject: str, grade: Optional[int] = None) -> str:
        """
        Объяснить учебную тему

        Args:
            topic: Тема для объяснения
            subject: Предмет (математика, физика и т.д.)
            grade: Класс (для адаптации сложности)

        Returns:
            str: Объяснение темы
        """
        prompt = f"""
Объясни тему "{topic}" по предмету "{subject}" для ученика {grade or 5} класса.

Требования:
1. Простым и понятным языком
2. С примерами из жизни
3. Пошагово, от простого к сложному
4. Добавь практические задачи для закрепления (2-3 штуки)

Формат ответа:
📚 Что это такое
🔍 Как это работает
💡 Примеры из жизни
✏️ Практические задачи
"""
        return await self.generate_response(prompt, user_grade=grade)

    async def solve_problem(self, problem_text: str, subject: str, show_steps: bool = True) -> str:
        """
        Решить задачу с пошаговым объяснением

        Args:
            problem_text: Текст задачи
            subject: Предмет
            show_steps: Показывать шаги решения

        Returns:
            str: Решение с объяснением
        """
        prompt = f"""
Реши задачу по предмету "{subject}":

{problem_text}

{'Покажи ПОДРОБНОЕ пошаговое решение с объяснением каждого шага.' if show_steps else 'Покажи только ответ и краткое объяснение.'}

Формат:
📝 Условие (кратко перескажи что дано)
🔢 Решение (пошагово)
✅ Ответ
💡 Почему так (объясни логику)
"""
        return await self.generate_response(prompt)

    async def check_answer(
        self, problem: str, user_answer: str, correct_answer: Optional[str] = None
    ) -> str:
        """
        Проверить ответ ученика и дать фидбек

        Args:
            problem: Условие задачи
            user_answer: Ответ ученика
            correct_answer: Правильный ответ (если известен)

        Returns:
            str: Фидбек с объяснением
        """
        prompt = f"""
Задача: {problem}

Ответ ученика: {user_answer}
{f'Правильный ответ: {correct_answer}' if correct_answer else ''}

Проверь ответ ученика:
1. Правильный ли ответ?
2. Если правильный — похвали и объясни почему
3. Если неправильный — объясни ошибку МЯГКО и подскажи как исправить
4. Дай совет как решать подобные задачи

Будь добрым и поддерживающим! 🐼
"""
        return await self.generate_response(prompt)

    def get_model_info(self) -> Dict[str, str]:
        """
        Получить информацию о модели (для отладки)
        НЕ РАСКРЫВАТЬ пользователям!

        Returns:
            Dict: Информация о модели и настройках
        """
        return {
            "model": settings.gemini_model,
            "temperature": str(settings.ai_temperature),
            "max_tokens": str(settings.ai_max_tokens),
            "public_name": "PandaPalAI",  # То, что видят пользователи
        }

    # ============ ОБРАБОТКА ИЗОБРАЖЕНИЙ ============

    def _prepare_image_for_gemini(self, image_data: bytes):
        """
        Подготовить изображение для отправки в Gemini API

        Args:
            image_data: Бинарные данные изображения

        Returns:
            PIL Image объект для Gemini
        """
        try:
            # Проверяем размер изображения
            if len(image_data) > 20 * 1024 * 1024:  # 20MB лимит
                raise ValueError("Изображение слишком большое (максимум 20MB)")

            # Конвертируем байты в PIL Image
            import io

            image = Image.open(io.BytesIO(image_data))

            logger.info(f"🖼️ Изображение подготовлено для анализа ({len(image_data)} байт)")
            return image

        except Exception as e:
            logger.error(f"❌ Ошибка подготовки изображения: {e}")
            raise ValueError(f"Не удалось обработать изображение: {e}")

    async def analyze_image(
        self,
        image_data: bytes,
        user_message: str = "",
        user_age: Optional[int] = None,
        user_grade: Optional[int] = None,
    ) -> str:
        """
        Анализировать изображение с помощью Gemini Vision API

        Args:
            image_data: Бинарные данные изображения
            user_message: Сообщение пользователя (опционально)
            user_age: Возраст ребёнка
            user_grade: Класс ребёнка

        Returns:
            str: Анализ изображения от AI
        """
        try:
            # Проверяем кэш для изображений
            image_hash = hashlib.md5(image_data).hexdigest()
            cache_key = f"image_analysis:{image_hash}:{user_message}"
            cached_response = await AIResponseCache.get_response(cache_key)

            if cached_response:
                logger.debug(f"💾 Анализ изображения получен из кэша")
                return cached_response

            # Подготавливаем изображение
            prepared_image = self._prepare_image_for_gemini(image_data)

            # Формируем промпт для анализа
            context_instruction = self._build_context_instruction(user_age, user_grade)

            if user_message:
                prompt = f"{context_instruction}\n\nПользователь прислал изображение и написал: '{user_message}'\n\nПроанализируй изображение и ответь на вопрос ребёнка, учитывая его возраст. Будь дружелюбным и образовательным."
            else:
                prompt = f"{context_instruction}\n\nРебёнок прислал изображение. Проанализируй его и расскажи что ты видишь, адаптируя объяснение под возраст ребёнка. Если это учебный материал (задача, схема, рисунок) - помоги с объяснением."

            # Отправляем запрос в Gemini с изображением и текстом
            model = genai.GenerativeModel(settings.gemini_model)
            response = model.generate_content([prepared_image, prompt])

            if not response.text:
                return "Извини, я не смог проанализировать это изображение. Попробуй отправить другое фото! 🐼"

            # Сохраняем в кэш
            await AIResponseCache.set_response(cache_key, response.text, ttl=3600)  # 1 час

            logger.info(f"🖼️ Изображение проанализировано успешно")
            return response.text

        except Exception as e:
            logger.error(f"❌ Ошибка анализа изображения: {e}")
            return "Извини, произошла ошибка при анализе изображения. Попробуй ещё раз! 🐼"

    async def moderate_image_content(self, image_data: bytes) -> tuple[bool, str]:
        """
        Проверить изображение на безопасность для детей

        Args:
            image_data: Бинарные данные изображения

        Returns:
            tuple[bool, str]: (безопасно, причина_блокировки)
        """
        try:
            # Подготавливаем изображение
            prepared_image = self._prepare_image_for_gemini(image_data)

            # Специальный промпт для модерации
            moderation_prompt = """
            Проанализируй это изображение на предмет безопасности для детей 6-18 лет.
            
            Проверь наличие:
            - Неподходящего контента (насилие, оружие, наркотики)
            - Взрослого контента (18+)
            - Опасных действий
            - Текст с запрещёнными словами
            
            Ответь только одним словом:
            - "SAFE" - если изображение безопасно
            - "BLOCK" - если изображение нужно заблокировать
            
            Если BLOCK, добавь причину через двоеточие: BLOCK: причина
            """

            model = genai.GenerativeModel(settings.gemini_model)
            response = model.generate_content([prepared_image, moderation_prompt])

            result = response.text.strip().upper()

            if result.startswith("SAFE"):
                return True, ""
            elif result.startswith("BLOCK:"):
                reason = result.replace("BLOCK:", "").strip()
                logger.warning(f"🚫 Изображение заблокировано: {reason}")
                return False, reason
            else:
                # Если ответ неожиданный, блокируем для безопасности
                logger.warning(f"🚫 Неожиданный ответ модерации изображения: {result}")
                return False, "Неопределённый контент"

        except Exception as e:
            logger.error(f"❌ Ошибка модерации изображения: {e}")
            # При ошибке блокируем для безопасности
            return False, "Ошибка проверки безопасности"

    async def create_educational_task_from_image(
        self,
        image_data: bytes,
        subject: str = "общий",
        user_age: Optional[int] = None,
        user_grade: Optional[int] = None,
    ) -> str:
        """
        Создать образовательную задачу на основе изображения

        Args:
            image_data: Бинарные данные изображения
            subject: Предмет (математика, физика, биология и т.д.)
            user_age: Возраст ребёнка
            user_grade: Класс ребёнка

        Returns:
            str: Образовательная задача с использованием изображения
        """
        try:
            # Подготавливаем изображение
            prepared_image = self._prepare_image_for_gemini(image_data)

            context_instruction = self._build_context_instruction(user_age, user_grade)

            prompt = f"""
            {context_instruction}
            
            На основе этого изображения создай образовательную задачу по предмету "{subject}".
            
            Задача должна быть:
            - Подходящей для возраста ребёнка
            - Интересной и понятной
            - Связанной с тем, что изображено на картинке
            - С чётким вопросом и возможностью ответа
            
            Формат:
            📝 Описание изображения
            ❓ Вопрос/задача
            💡 Подсказка (если нужна)
            
            Будь креативным и образовательным! 🎓
            """

            model = genai.GenerativeModel(settings.gemini_model)
            response = model.generate_content([prepared_image, prompt])

            logger.info(f"🎓 Создана образовательная задача на основе изображения")
            return response.text

        except Exception as e:
            logger.error(f"❌ Ошибка создания задачи из изображения: {e}")
            return "Извини, не удалось создать задачу на основе этого изображения. Попробуй другое фото! 🐼"

    def _build_context_instruction(self, user_age: Optional[int], user_grade: Optional[int]) -> str:
        """
        Формирует инструкцию для AI на основе возраста и класса пользователя.
        """
        context_parts = []
        if user_age:
            context_parts.append(f"Возраст ребёнка: {user_age} лет.")
        if user_grade:
            context_parts.append(f"Класс обучения: {user_grade}.")

        if context_parts:
            return (
                "Учитывай, что ты общаешься с ребёнком. "
                + " ".join(context_parts)
                + " Адаптируй свой язык, сложность и примеры под этот уровень."
            )
        return "Ты общаешься с ребёнком. Адаптируй свой язык, сложность и примеры."
