"""
Генератор ответов AI - отвечает только за генерацию текста
Соблюдает принцип Single Responsibility Principle
"""

import google.generativeai as genai
from typing import Dict, List, Optional

from bot.config import AI_SYSTEM_PROMPT, settings
from loguru import logger


class AIResponseGenerator:
    """Генератор ответов AI - только генерация текста"""

    def __init__(self):
        """Инициализация генератора"""
        genai.configure(api_key=settings.gemini_api_key)

        self.generation_config = {
            "temperature": settings.ai_temperature,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": settings.ai_max_tokens,
        }

        self.safety_settings = [
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
        ]

        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
            system_instruction=AI_SYSTEM_PROMPT,
        )

        logger.info(f"✅ AI Response Generator инициализирован: {settings.gemini_model}")

    async def generate_text_response(
        self, user_message: str, chat_history: List[Dict[str, str]] = None
    ) -> str:
        """Генерация текстового ответа"""
        try:
            # Подготовка истории для контекста
            history_text = ""
            if chat_history:
                history_text = "\n".join(
                    [
                        f"{msg['role']}: {msg['content']}"
                        for msg in chat_history[-10:]  # Последние 10 сообщений
                    ]
                )

            # Формирование промпта с контекстом
            full_prompt = f"{history_text}\nUser: {user_message}\nAssistant:"

            # Генерация ответа
            response = await self.model.generate_content_async(full_prompt)

            if response and response.text:
                return response.text.strip()
            else:
                return "Извините, не могу сгенерировать ответ в данный момент."

        except Exception as e:
            logger.error(f"Ошибка генерации AI: {e}")
            return "Извините, произошла ошибка при генерации ответа."

    async def generate_image_response(self, image_data: bytes, prompt: str) -> str:
        """Генерация ответа на изображение"""
        try:
            # Конвертация изображения
            image = genai.types.Part.from_data(data=image_data, mime_type="image/jpeg")

            # Генерация ответа
            response = await self.model.generate_content_async([image, prompt])

            if response and response.text:
                return response.text.strip()
            else:
                return "Не могу проанализировать изображение."

        except Exception as e:
            logger.error(f"Ошибка анализа изображения: {e}")
            return "Извините, не могу проанализировать изображение."
