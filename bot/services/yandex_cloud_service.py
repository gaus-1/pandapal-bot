"""
Сервис интеграции с Yandex Cloud AI.

Объединяет все AI возможности Yandex Cloud:
- YandexGPT (текстовые ответы)
- SpeechKit (распознавание речи)
- Vision (анализ изображений)

Для образовательного бота PandaPal.
"""

import base64
import json
from typing import Any, Dict, List, Optional

import requests
from loguru import logger

from bot.config import settings


class YandexCloudService:
    """
    Единый сервис для работы с Yandex Cloud AI.

    Возможности:
    - Генерация текстовых ответов (YandexGPT)
    - Распознавание речи (SpeechKit STT)
    - Анализ изображений (Vision OCR)
    """

    def __init__(self):
        """Инициализация сервиса Yandex Cloud."""
        self.api_key = settings.yandex_cloud_api_key
        self.folder_id = settings.yandex_cloud_folder_id
        self.gpt_model = settings.yandex_gpt_model

        # Endpoints Yandex Cloud
        self.gpt_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.stt_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        self.vision_url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"

        # Заголовки для всех запросов
        self.headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"✅ YandexCloudService инициализирован: модель {self.gpt_model}")

    # ============================================================================
    # YANDEXGPT - ТЕКСТОВЫЕ ОТВЕТЫ
    # ============================================================================

    async def generate_text_response(
        self,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Генерация текстового ответа через YandexGPT.

        Args:
            user_message: Сообщение пользователя
            chat_history: История чата [{"role": "user/assistant", "text": "..."}]
            system_prompt: Системный промпт (инструкция для AI)
            temperature: Креативность (0.0-1.0)
            max_tokens: Максимальная длина ответа

        Returns:
            str: Ответ от YandexGPT
        """
        try:
            # Формируем историю сообщений
            messages = []

            # Добавляем системный промпт
            if system_prompt:
                messages.append({"role": "system", "text": system_prompt})

            # Добавляем историю чата
            if chat_history:
                for msg in chat_history[-10:]:  # Последние 10 сообщений
                    messages.append({"role": msg.get("role", "user"), "text": msg.get("text", "")})

            # Добавляем текущее сообщение
            messages.append({"role": "user", "text": user_message})

            # Формируем запрос к YandexGPT
            payload = {
                "modelUri": f"gpt://{self.folder_id}/{self.gpt_model}/latest",
                "completionOptions": {
                    "stream": False,
                    "temperature": temperature,
                    "maxTokens": str(max_tokens),
                },
                "messages": messages,
            }

            logger.info(f"📤 YandexGPT запрос: {len(user_message)} символов")

            # Отправляем запрос
            response = requests.post(self.gpt_url, headers=self.headers, json=payload, timeout=30)

            response.raise_for_status()
            result = response.json()

            # Извлекаем ответ
            ai_response = result["result"]["alternatives"][0]["message"]["text"]

            logger.info(f"✅ YandexGPT ответ: {len(ai_response)} символов")
            return ai_response

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка YandexGPT API: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка YandexGPT: {e}")
            raise

    # ============================================================================
    # SPEECHKIT STT - РАСПОЗНАВАНИЕ РЕЧИ
    # ============================================================================

    async def recognize_speech(
        self, audio_data: bytes, audio_format: str = "oggopus", language: str = "ru-RU"
    ) -> str:
        """
        Распознавание речи через SpeechKit STT.

        Args:
            audio_data: Аудио в байтах (OGG, MP3, WAV)
            audio_format: Формат аудио (oggopus, mp3, lpcm)
            language: Язык распознавания (ru-RU, en-US)

        Returns:
            str: Распознанный текст
        """
        try:
            logger.info(f"🎤 SpeechKit STT: распознавание {len(audio_data)} байт")

            # Формируем параметры запроса
            params = {
                "topic": "general",  # Общая тема
                "lang": language,
                "format": audio_format,
                "sampleRateHertz": "48000" if audio_format == "oggopus" else "16000",
            }

            # Отправляем аудио
            response = requests.post(
                self.stt_url,
                headers={
                    "Authorization": f"Api-Key {self.api_key}",
                },
                params=params,
                data=audio_data,
                timeout=30,
            )

            response.raise_for_status()
            result = response.json()

            # Извлекаем текст
            recognized_text = result.get("result", "")

            logger.info(f"✅ SpeechKit STT: '{recognized_text}'")
            return recognized_text

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка SpeechKit STT: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка SpeechKit: {e}")
            raise

    # ============================================================================
    # VISION OCR - АНАЛИЗ ИЗОБРАЖЕНИЙ
    # ============================================================================

    async def analyze_image_with_text(
        self, image_data: bytes, user_question: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Анализ изображения: OCR + описание через YandexGPT.

        Args:
            image_data: Изображение в байтах
            user_question: Вопрос пользователя об изображении

        Returns:
            dict: {
                "text": "распознанный текст",
                "description": "описание от GPT",
                "analysis": "анализ для школьника"
            }
        """
        try:
            logger.info(f"📷 Vision OCR: анализ {len(image_data)} байт")

            # Шаг 1: Распознаём текст на изображении
            image_base64 = base64.b64encode(image_data).decode("utf-8")

            vision_payload = {
                "folderId": self.folder_id,
                "analyze_specs": [
                    {
                        "content": image_base64,
                        "features": [
                            {
                                "type": "TEXT_DETECTION",
                                "text_detection_config": {"language_codes": ["ru", "en"]},
                            }
                        ],
                    }
                ],
            }

            response = requests.post(
                self.vision_url, headers=self.headers, json=vision_payload, timeout=30
            )

            response.raise_for_status()
            vision_result = response.json()

            # Извлекаем распознанный текст (ВСЕ строки, не только первую!)
            recognized_text = ""
            try:
                text_annotation = vision_result["results"][0]["results"][0]["textDetection"]

                # Собираем ВСЕ строки текста с изображения
                all_lines = []
                for page in text_annotation.get("pages", []):
                    for block in page.get("blocks", []):
                        for line in block.get("lines", []):
                            line_text = line.get("text", "").strip()
                            if line_text:
                                all_lines.append(line_text)

                recognized_text = "\n".join(all_lines)

            except (KeyError, IndexError) as e:
                logger.warning(f"⚠️ Текст на изображении не найден: {e}")

            logger.info(f"✅ Vision OCR: распознано {len(recognized_text)} символов")

            # Если текст не распознан - просим переснять
            if not recognized_text or len(recognized_text) < 10:
                return {
                    "recognized_text": "",
                    "analysis": (
                        "📷 Я не смог четко разглядеть текст на фотографии.\n\n"
                        "Пожалуйста, сфотографируй задание еще раз:\n"
                        "✅ При хорошем освещении\n"
                        "✅ Четко и ровно\n"
                        "✅ Крупным планом\n"
                        "✅ Без бликов и теней\n\n"
                        "Или попробуй написать задачу текстом! 📝"
                    ),
                    "has_text": False,
                }

            # Шаг 2: Решаем через YandexGPT
            analysis_prompt = f"""
            На фотографии школьное задание. Распознанный текст:
            "{recognized_text}"

            Вопрос ученика: {user_question or "Реши задачи"}

            ТВОЯ ЗАДАЧА - ПОЛНОСТЬЮ РЕШИТЬ ВСЕ ЗАДАЧИ/УРАВНЕНИЯ/ПРИМЕРЫ:

            1. ПРОЧИТАЙ внимательно каждую задачу с фото
            2. РЕШИ КАЖДУЮ ЗАДАЧУ пошагово:
               - Что дано
               - Что нужно найти
               - Решение (все шаги подробно!)
               - ОТВЕТ (конкретное число!)

            3. Если это уравнение - РЕШИ и дай ОТВЕТ
            4. Если это примеры - ПОСЧИТАЙ и дай ОТВЕТЫ
            5. Если это задачи со словами - РЕШИ и дай КОНКРЕТНЫЕ ОТВЕТЫ

            ОБЯЗАТЕЛЬНО:
            - Реши ВСЕ задачи по порядку
            - Пиши шаги решения просто и понятно
            - В конце каждой задачи пиши: "Ответ: ..."
            - БЕЗ символов $ и LaTeX!
            - Используй простой текст и эмодзи

            ФОРМАТ ОТВЕТА:
            📝 Задача 1:
            Дано: ...
            Решение: ...
            Ответ: ... ✅

            📝 Задача 2:
            ...
            """

            gpt_analysis = await self.generate_text_response(
                user_message=analysis_prompt,
                system_prompt=(
                    "Ты помощник-репетитор для детей 1-9 класса. "
                    "РЕШАЙ задачи ПОЛНОСТЬЮ, а не только подсказывай! "
                    "Объясняй каждый шаг ПРОСТО, используй эмодзи. "
                    "ВСЕГДА давай конкретные ОТВЕТЫ. "
                    "БЕЗ LaTeX, БЕЗ символа $, только простой текст!"
                ),
                temperature=0.3,  # Меньше креативности, больше точности
            )

            return {
                "recognized_text": recognized_text,
                "analysis": gpt_analysis,
                "has_text": bool(recognized_text),
            }

        except Exception as e:
            logger.error(f"❌ Ошибка Vision + GPT: {e}")
            raise

    # ============================================================================
    # УТИЛИТЫ
    # ============================================================================

    def get_model_info(self) -> Dict[str, str]:
        """Информация о текущей модели."""
        return {
            "provider": "Yandex Cloud",
            "model": self.gpt_model,
            "capabilities": "text, speech, vision",
            "language": "ru, en",
        }


# ============================================================================
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР (SINGLETON)
# ============================================================================

_yandex_service: Optional[YandexCloudService] = None


def get_yandex_cloud_service() -> YandexCloudService:
    """Получить глобальный экземпляр Yandex Cloud сервиса."""
    global _yandex_service
    if _yandex_service is None:
        _yandex_service = YandexCloudService()
    return _yandex_service
