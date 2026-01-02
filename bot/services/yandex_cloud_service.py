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

import httpx
from loguru import logger

from bot.config import settings
from bot.services.ai_request_queue import get_ai_request_queue


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

        # Таймаут для всех запросов (30 секунд)
        self.timeout = httpx.Timeout(30.0, connect=10.0)

        # Очередь для управления одновременными запросами
        # Максимум 12 одновременных запросов для баланса между производительностью
        # и защитой от rate limiting Yandex Cloud API
        self.request_queue = get_ai_request_queue(max_concurrent=12)

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

            # Внутренняя функция для выполнения запроса (оборачивается в очередь)
            async def _execute_request():
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(self.gpt_url, headers=self.headers, json=payload)
                    response.raise_for_status()
                    result = response.json()
                    return result

            # Выполняем запрос через очередь для контроля параллелизма
            result = await self.request_queue.process(_execute_request)

            # Извлекаем ответ
            ai_response = result["result"]["alternatives"][0]["message"]["text"]

            logger.info(f"✅ YandexGPT ответ: {len(ai_response)} символов")
            return ai_response

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Ошибка YandexGPT API (HTTP {e.response.status_code}): {e}")
            if e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"❌ Таймаут YandexGPT API: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"❌ Ошибка запроса YandexGPT API: {e}")
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
            }

            # sampleRateHertz нужен ТОЛЬКО для lpcm (по документации Yandex SpeechKit)
            # Для oggopus его НЕ нужно передавать
            if audio_format == "lpcm":
                params["sampleRateHertz"] = "16000"

            # Внутренняя функция для выполнения запроса (оборачивается в очередь)
            async def _execute_request():
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.stt_url,
                        headers={
                            "Authorization": f"Api-Key {self.api_key}",
                        },
                        params=params,
                        content=audio_data,
                    )
                    response.raise_for_status()
                    return response.json()

            # Выполняем запрос через очередь для контроля параллелизма
            result = await self.request_queue.process(_execute_request)

            # Извлекаем текст
            recognized_text = result.get("result", "")

            logger.info(f"✅ SpeechKit STT: '{recognized_text}'")
            return recognized_text

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Ошибка SpeechKit STT (HTTP {e.response.status_code}): {e}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"❌ Таймаут SpeechKit STT: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"❌ Ошибка запроса SpeechKit STT: {e}")
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

            # Внутренняя функция для выполнения запроса (оборачивается в очередь)
            async def _execute_request():
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.vision_url, headers=self.headers, json=vision_payload
                    )
                    response.raise_for_status()
                    return response.json()

            # Выполняем запрос через очередь для контроля параллелизма
            vision_result = await self.request_queue.process(_execute_request)

            # 🔍 ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ для отладки
            logger.info(f"📊 Vision API response keys: {list(vision_result.keys())}")

            # Логируем ПОЛНЫЙ ответ для анализа структуры
            response_full = json.dumps(vision_result, ensure_ascii=False, indent=2)
            response_preview = response_full[:2000]  # Первые 2000 символов
            logger.info(
                f"📊 ПОЛНЫЙ Vision API response (первые 2000 символов):\n{response_preview}"
            )

            # Сохраняем полный ответ для детального анализа
            logger.debug(f"📊 ВЕСЬ Vision API response:\n{response_full}")

            # Извлекаем распознанный текст (ВСЕ строки, не только первую!)
            recognized_text = ""
            all_lines = []

            try:
                # Пытаемся получить текст разными способами
                results = vision_result.get("results", [])
                logger.info(f"📊 Results length: {len(results)}")

                if results and len(results) > 0:
                    inner_results = results[0].get("results", [])
                    logger.info(f"📊 Inner results length: {len(inner_results)}")

                    if inner_results and len(inner_results) > 0:
                        text_detection = inner_results[0].get("textDetection", {})
                        logger.info(f"📊 Text detection keys: {list(text_detection.keys())}")

                        pages = text_detection.get("pages", [])
                        logger.info(f"📄 Найдено страниц: {len(pages)}")

                        for page_idx, page in enumerate(pages):
                            blocks = page.get("blocks", [])
                            logger.info(f"📦 Страница {page_idx}: блоков {len(blocks)}")

                            for block_idx, block in enumerate(blocks):
                                lines = block.get("lines", [])
                                logger.info(f"  📦 Блок {block_idx}: строк {len(lines)}")

                                # Логируем структуру первого блока для анализа
                                if block_idx == 0 and lines:
                                    logger.info(
                                        f"  🔍 Структура первой строки: {list(lines[0].keys())}"
                                    )

                                for line_idx, line in enumerate(lines):
                                    # СПОСОБ 1: Прямой текст (line["text"])
                                    line_text = line.get("text", "").strip()

                                    # СПОСОБ 2: Если текста нет, собираем из words
                                    if not line_text and "words" in line:
                                        words = []
                                        for word in line.get("words", []):
                                            word_text = word.get("text", "").strip()
                                            if word_text:
                                                words.append(word_text)
                                        if words:
                                            line_text = " ".join(words)

                                    # СПОСОБ 3: Если и words нет, проверяем alternatives
                                    if not line_text and "alternatives" in line:
                                        for alt in line.get("alternatives", []):
                                            alt_text = alt.get("text", "").strip()
                                            if alt_text:
                                                line_text = alt_text
                                                break

                                    if line_text:
                                        all_lines.append(line_text)
                                        logger.info(f"    ✅ Строка {line_idx}: {line_text[:80]}")
                                    else:
                                        logger.warning(
                                            f"    ⚠️ Строка {line_idx} пустая! Ключи: {list(line.keys())}"
                                        )

                recognized_text = "\n".join(all_lines)

                if recognized_text:
                    logger.info(
                        f"✅ Vision OCR УСПЕШНО: {len(recognized_text)} символов, {len(all_lines)} строк"
                    )
                    logger.info(f"📝 Первые 200 символов:\n{recognized_text[:200]}")
                else:
                    logger.warning("⚠️ Vision API вернул ответ, но текст пустой!")
                    logger.warning(f"⚠️ Проверьте структуру: {response_preview}")

            except (KeyError, IndexError, AttributeError) as e:
                logger.error(f"❌ Ошибка парсинга Vision API: {type(e).__name__}: {e}")
                logger.error(f"❌ Response structure: {response_preview}")

            # ВАЖНО: Не обрываем процесс даже если OCR распознал мало текста!
            # YandexGPT попробует работать с тем что есть

            # Если текст совсем не распознан - даем подробный совет
            if not recognized_text:
                logger.warning("⚠️ OCR не распознал НИКАКОГО текста на изображении")
                return {
                    "recognized_text": "",
                    "analysis": (
                        "📷 **Разбор задания:**\n"
                        "📸 Я не смог распознать текст на фотографии.\n\n"
                        "💡 **Совет:** Лучше фотографировать **БУМАГУ**, а не экран!\n\n"
                        "**Как сделать хорошее фото:**\n"
                        "✅ При хорошем освещении\n"
                        "✅ Четко и ровно (не под углом)\n"
                        "✅ Крупным планом\n"
                        "✅ Без бликов и теней\n"
                        "✅ Текст должен быть четким\n\n"
                        "**Или проще:**\n"
                        "📝 Напиши задачи **текстом** — так будет точнее и быстрее! ✨"
                    ),
                    "has_text": False,
                }

            # Если текст короткий - предупреждаем, но всё равно пробуем
            if len(recognized_text) < 20:
                logger.warning(
                    f"⚠️ OCR распознал мало текста ({len(recognized_text)} символов): '{recognized_text}'"
                )

            # Шаг 2: Решаем через YandexGPT (даже если текста мало)
            logger.info(
                f"🤖 Отправляю распознанный текст ({len(recognized_text)} символов) в YandexGPT"
            )

            analysis_prompt = f"""
На фотографии школьное задание или учебный материал.

РАСПОЗНАННЫЙ ТЕКСТ с изображения:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{recognized_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Вопрос ученика: {user_question or "Объясни что здесь написано и помоги разобраться"}

ТВОЯ ЗАДАЧА:

1️⃣ Если это ЗАДАЧИ/ПРИМЕРЫ/УРАВНЕНИЯ:
   - Реши КАЖДУЮ задачу полностью
   - Покажи ВСЕ шаги решения
   - Дай КОНКРЕТНЫЙ ОТВЕТ (число, результат)

2️⃣ Если это РЕЦЕПТ/ИНСТРУКЦИЯ:
   - Объясни простыми словами что нужно делать
   - Разбей на понятные шаги
   - Дай полезные советы

3️⃣ Если это ПРАВИЛО/ОПРЕДЕЛЕНИЕ:
   - Объясни своими словами
   - Приведи простые примеры
   - Помоги запомнить

ВАЖНО:
✅ Работай с распознанным текстом (даже если он неполный)
✅ Если чего-то не хватает - скажи об этом и работай с тем что есть
✅ Пиши ПРОСТО и ПОНЯТНО для детей 1-9 класса
✅ Используй эмодзи для наглядности 😊
✅ БЕЗ символов $ и LaTeX - только простой текст!
✅ Давай КОНКРЕТНЫЕ ответы, а не только подсказки

ФОРМАТ ОТВЕТА:

📝 **[Название задачи/темы]**

**Что здесь:**
[краткое описание]

**Решение:**
[подробные шаги]

**Ответ:** [конкретный результат] ✅

Если есть еще задачи - решаем их по очереди!
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
