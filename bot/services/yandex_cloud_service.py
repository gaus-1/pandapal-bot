"""
Сервис интеграции с Yandex Cloud AI.

Объединяет YandexGPT, SpeechKit и Vision API.
"""

import base64
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from bot.config import settings
from bot.services.ai_request_queue import get_ai_request_queue
from bot.services.circuit_breaker import (
    CircuitOpenError,
    yandex_gpt_circuit,
    yandex_stt_circuit,
    yandex_vision_circuit,
)


class YandexCloudService:
    """Единый сервис для работы с Yandex Cloud AI."""

    def __init__(self):
        """Инициализация сервиса Yandex Cloud."""
        self.api_key = settings.yandex_cloud_api_key
        self.folder_id = settings.yandex_cloud_folder_id
        self.gpt_model = settings.yandex_gpt_model

        # Endpoints Yandex Cloud
        self.gpt_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.stt_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        self.vision_url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
        self.embedding_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding"

        # Заголовки для всех запросов
        self.headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
            "x-data-logging-enabled": "true",  # Для диагностики ошибок Yandex Cloud
        }

        # Таймаут для всех запросов (30 секунд)
        self.timeout = httpx.Timeout(30.0, connect=10.0)

        # Персистентные httpx-клиенты (переиспользуем TCP-соединения вместо создания новых на каждый запрос)
        self._client = httpx.AsyncClient(timeout=self.timeout)
        self._stt_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0))

        # Очередь для управления одновременными запросами
        # Максимум 12 одновременных запросов для баланса между производительностью
        # и защитой от rate limiting Yandex Cloud API
        self.request_queue = get_ai_request_queue(max_concurrent=12)

        logger.info(f"✅ YandexCloudService инициализирован: модель {self.gpt_model}")

    async def close(self) -> None:
        """Закрыть персистентные HTTP-клиенты."""
        await self._client.aclose()
        await self._stt_client.aclose()
        logger.info("✅ YandexCloudService HTTP-клиенты закрыты")

    def _extract_text_from_line(self, line: dict[str, Any]) -> str:
        """
        Извлечь текст из строки Vision API (уменьшает вложенность).

        Args:
            line: Строка из Vision API response

        Returns:
            str: Распознанный текст или пустая строка
        """
        # СПОСОБ 1: Прямой текст (line["text"])
        line_text = line.get("text", "").strip()
        if line_text:
            return line_text

        # СПОСОБ 2: Если текста нет, собираем из words
        if "words" in line:
            words = []
            for word in line.get("words", []):
                word_text = word.get("text", "").strip()
                if word_text:
                    words.append(word_text)
            if words:
                return " ".join(words)

        # СПОСОБ 3: Если и words нет, проверяем alternatives
        if "alternatives" in line:
            for alt in line.get("alternatives", []):
                alt_text = alt.get("text", "").strip()
                if alt_text:
                    return alt_text

        return ""

    def _parse_streaming_chunk(self, line: str):
        """
        Парсинг одного chunk из streaming ответа YandexGPT.

        Args:
            line: Строка из streaming ответа

        Yields:
            str: Извлеченный текст из chunk
        """
        # YandexGPT streaming может возвращать в разных форматах
        # Вариант 1: JSON chunk напрямую
        # Вариант 2: SSE формат "data: {...}"
        try:
            # Убираем префикс "data: " если есть (SSE формат)
            json_line = line[6:] if line.startswith("data: ") else line
            chunk_data = json.loads(json_line)

            # Извлекаем текст из chunk
            # Формат может быть:
            # {"result": {"alternatives": [{"message": {"text": "chunk"}}]}}
            # или {"alternatives": [{"message": {"text": "chunk"}}]}
            result = chunk_data.get("result", chunk_data)
            if not isinstance(result, dict):
                return

            alternatives = result.get("alternatives", [])
            if not alternatives or not isinstance(alternatives, list):
                return

            for alt in alternatives:
                if not isinstance(alt, dict):
                    continue

                message = alt.get("message", {})
                if not isinstance(message, dict):
                    continue

                text = message.get("text", "")
                if text and isinstance(text, str):
                    yield text

        except json.JSONDecodeError:
            logger.debug(f"⚠️ Пропущен не-JSON chunk: {line[:100]}")
        except Exception as e:
            logger.debug(f"⚠️ Ошибка парсинга chunk: {e}, line: {line[:100]}")

    def _extract_text_from_vision_result(self, vision_result: dict[str, Any]) -> str:
        """
        Извлечь весь распознанный текст из Vision API response.

        Args:
            vision_result: Полный ответ Vision API

        Returns:
            str: Распознанный текст, объединенный из всех строк
        """
        all_lines = []
        try:
            results = vision_result.get("results", [])
            logger.debug(f"📊 Results length: {len(results)}")

            if not results:
                return ""

            inner_results = results[0].get("results", [])
            logger.debug(f"📊 Inner results length: {len(inner_results)}")

            if not inner_results:
                return ""

            text_detection = inner_results[0].get("textDetection", {})
            logger.debug(f"📊 Text detection keys: {list(text_detection.keys())}")

            pages = text_detection.get("pages", [])
            logger.debug(f"📄 Найдено страниц: {len(pages)}")

            for page_idx, page in enumerate(pages):
                blocks = page.get("blocks", [])
                logger.debug(f"📦 Страница {page_idx}: блоков {len(blocks)}")

                for block_idx, block in enumerate(blocks):
                    lines = block.get("lines", [])
                    logger.debug(f"  📦 Блок {block_idx}: строк {len(lines)}")

                    if block_idx == 0 and lines:
                        logger.debug(f"  🔍 Структура первой строки: {list(lines[0].keys())}")

                    for line_idx, line in enumerate(lines):
                        line_text = self._extract_text_from_line(line)
                        if line_text:
                            all_lines.append(line_text)
                            logger.debug(f"    ✅ Строка {line_idx}: {line_text[:80]}")
                        else:
                            logger.debug(
                                f"    ⚠️ Строка {line_idx} пустая! Ключи: {list(line.keys())}"
                            )

            recognized_text = "\n".join(all_lines)
            if recognized_text:
                logger.info(
                    f"✅ Vision OCR УСПЕШНО: {len(recognized_text)} символов, {len(all_lines)} строк"
                )
            return recognized_text

        except Exception as e:
            logger.error(f"❌ Ошибка извлечения текста из Vision API: {e}", exc_info=True)
            return ""

    # YandexGPT - текстовые ответы

    async def generate_text_response(
        self,
        user_message: str,
        chat_history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.35,
        max_tokens: int = 8192,
        model: str | None = None,
    ) -> str:
        """
        Генерация текстового ответа через YandexGPT.

        Args:
            user_message: Сообщение пользователя
            chat_history: История чата [{"role": "user/assistant", "text": "..."}]
            system_prompt: Системный промпт (инструкция для AI)
            temperature: Креативность (0.0-1.0)
            max_tokens: Максимальная длина ответа
            model: Модель YandexGPT (yandexgpt-lite или yandexgpt-pro). Если None, используется self.gpt_model

        Returns:
            str: Ответ от YandexGPT
        """
        try:
            # Используем переданную модель или дефолтную
            model_name = model if model else self.gpt_model

            # Формируем историю сообщений
            messages = []

            # Добавляем системный промпт
            if system_prompt:
                messages.append({"role": "system", "text": system_prompt})

            # Добавляем историю чата (срез по лимиту делается у вызывающей стороны)
            if chat_history:
                for msg in chat_history:
                    messages.append({"role": msg.get("role", "user"), "text": msg.get("text", "")})

            # Добавляем текущее сообщение
            messages.append({"role": "user", "text": user_message})

            # Формируем запрос к YandexGPT
            # По документации Yandex Cloud maxTokens должен быть строкой для всех моделей
            # Название модели уже содержит /latest или /rc (например: yandexgpt/latest или yandexgpt/rc)
            # Итоговый формат: gpt://folder_id/yandexgpt/latest (как в примере Yandex Cloud Console)
            model_uri = f"gpt://{self.folder_id}/{model_name}"
            # reasoningOptions (ENABLED_HIDDEN, reasoningEffort) — только для gpt-oss-120b.
            # yandexgpt/rc не поддерживает: "The model does not support reasoning".
            # CoT реализован через промпты (prompts.py + "Давайте решать пошагово" для задач).
            payload = {
                "modelUri": model_uri,
                "completionOptions": {
                    "stream": False,
                    "temperature": temperature,
                    "maxTokens": str(max_tokens),  # Строка по документации Yandex Cloud
                },
                "messages": messages,
            }

            logger.info(
                f"📤 YandexGPT запрос ({model_name}): modelUri={model_uri}, "
                f"{len(user_message)} символов, temp={temperature}, max_tokens={max_tokens}"
            )

            # Внутренняя функция для выполнения запроса (оборачивается в очередь)
            @retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=8),
                retry=retry_if_exception_type((httpx.TimeoutException, httpx.RequestError)),
                before_sleep=lambda rs: logger.warning(
                    f"🔄 YandexGPT retry {rs.attempt_number}/3: {rs.outcome.exception()}"
                ),
                reraise=True,
            )
            async def _execute_request():
                # Добавляем динамический request ID для диагностики
                request_headers = {
                    **self.headers,
                    "x-client-request-id": str(uuid.uuid4()),
                }
                response = await self._client.post(
                    self.gpt_url, headers=request_headers, json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result

            # Выполняем запрос через Circuit Breaker + очередь
            async def _cb_request():
                return await self.request_queue.process(_execute_request)

            result = await yandex_gpt_circuit.call(_cb_request)

            # Извлекаем ответ
            ai_response = result["result"]["alternatives"][0]["message"]["text"]

            logger.info(f"✅ YandexGPT ответ: {len(ai_response)} символов")
            return ai_response

        except CircuitOpenError as e:
            logger.warning(f"⚡ YandexGPT Circuit Breaker: {e}")
            return "Сервис временно перегружен. Попробуй через минуту 🐼"
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

    async def generate_text_response_stream(
        self,
        user_message: str,
        chat_history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.35,
        max_tokens: int = 8192,
        model: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Генерация текстового ответа через YandexGPT с streaming.

        Args:
            user_message: Сообщение пользователя
            chat_history: История чата [{"role": "user/assistant", "text": "..."}]
            system_prompt: Системный промпт (инструкция для AI)
            temperature: Креативность (0.0-1.0)
            max_tokens: Максимальная длина ответа
            model: Модель YandexGPT (yandexgpt-lite или yandexgpt-pro). Если None, используется self.gpt_model

        Yields:
            str: Chunks текста от YandexGPT по мере генерации
        """
        try:
            # Используем переданную модель или дефолтную
            model_name = model if model else self.gpt_model

            # Формируем историю сообщений
            messages = []

            # Добавляем системный промпт
            if system_prompt:
                messages.append({"role": "system", "text": system_prompt})

            # Добавляем историю чата (срез по лимиту делается у вызывающей стороны)
            if chat_history:
                for msg in chat_history:
                    messages.append({"role": msg.get("role", "user"), "text": msg.get("text", "")})

            # Добавляем текущее сообщение
            messages.append({"role": "user", "text": user_message})

            # Формируем запрос к YandexGPT с streaming
            # По документации Yandex Cloud maxTokens должен быть строкой для всех моделей
            # Название модели уже содержит /latest или /rc (например: yandexgpt/latest или yandexgpt/rc)
            # Итоговый формат: gpt://folder_id/yandexgpt/latest (как в примере Yandex Cloud Console)
            model_uri = f"gpt://{self.folder_id}/{model_name}"
            payload = {
                "modelUri": model_uri,
                "completionOptions": {
                    "stream": True,  # Включаем streaming
                    "temperature": temperature,
                    "maxTokens": str(max_tokens),  # Строка по документации Yandex Cloud
                },
                "messages": messages,
            }

            logger.info(
                f"📤 YandexGPT streaming запрос ({model_name}): modelUri={model_uri}, "
                f"{len(user_message)} символов, temp={temperature}, max_tokens={max_tokens}"
            )

            # Внутренняя функция для выполнения streaming запроса
            async def _execute_streaming_request():
                # Добавляем динамический request ID для диагностики
                request_headers = {
                    **self.headers,
                    "x-client-request-id": str(uuid.uuid4()),
                }
                async with (
                    self._client.stream(
                        "POST", self.gpt_url, headers=request_headers, json=payload
                    ) as response,
                ):
                    # Проверяем статус ДО чтения stream
                    if response.status_code != 200:
                        # Читаем ошибку ДО выброса исключения (для streaming response используем aiter_bytes)
                        error_text = ""
                        try:
                            error_bytes = b""
                            async for chunk in response.aiter_bytes():
                                error_bytes += chunk
                                if len(error_bytes) > 10000:  # Ограничиваем размер ошибки
                                    break
                            error_text = (
                                error_bytes.decode("utf-8", errors="ignore") if error_bytes else ""
                            )
                            # Пытаемся распарсить JSON ошибку
                            try:
                                import json

                                error_json = json.loads(error_text) if error_text else {}
                                error_message = error_json.get("error", {}).get(
                                    "message", error_text
                                )
                                error_text = error_message if error_message else error_text
                            except Exception:
                                pass  # Если не JSON, оставляем как есть
                        except Exception as read_err:
                            logger.debug(f"⚠️ Не удалось прочитать ошибку: {read_err}")
                            error_text = f"<unable to read response: {read_err}>"

                        logger.error(
                            f"❌ YandexGPT streaming API вернул HTTP {response.status_code}: {error_text[:500]}"
                        )
                        # Поднимаем исключение с полной информацией
                        response.raise_for_status()
                        return  # Не должно достичь сюда, но на всякий случай

                    buffer = ""
                    async for chunk_bytes in response.aiter_bytes():
                        # Декодируем байты в строку
                        try:
                            buffer += chunk_bytes.decode("utf-8", errors="ignore")
                        except UnicodeDecodeError:
                            continue

                        # Обрабатываем все полные строки из буфера
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()

                            if not line:
                                continue

                            # Обрабатываем chunk через отдельный метод
                            for text_chunk in self._parse_streaming_chunk(line):
                                yield text_chunk

            # Выполняем streaming запрос через очередь
            async for chunk in self.request_queue.process_stream(_execute_streaming_request):
                yield chunk

            logger.info("✅ YandexGPT streaming завершен")

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Ошибка YandexGPT streaming API (HTTP {e.response.status_code}): {e}")
            # Для streaming response нельзя просто так читать .text
            # Ошибка уже прочитана в _execute_streaming_request
            raise
        except httpx.TimeoutException as e:
            logger.error(f"❌ Таймаут YandexGPT streaming API: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"❌ Ошибка запроса YandexGPT streaming API: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка YandexGPT streaming: {e}")
            raise

    # SpeechKit STT - распознавание речи

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
            @retry(
                stop=stop_after_attempt(2),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                retry=retry_if_exception_type((httpx.TimeoutException, httpx.RequestError)),
                before_sleep=lambda rs: logger.warning(
                    f"🔄 SpeechKit retry {rs.attempt_number}/2: {rs.outcome.exception()}"
                ),
                reraise=True,
            )
            async def _execute_request():
                response = await self._stt_client.post(
                    self.stt_url,
                    headers={
                        "Authorization": f"Api-Key {self.api_key}",
                    },
                    params=params,
                    content=audio_data,
                )
                response.raise_for_status()
                return response.json()

            # Выполняем запрос через Circuit Breaker + очередь
            async def _cb_request():
                return await self.request_queue.process(_execute_request)

            result = await yandex_stt_circuit.call(_cb_request)

            # Извлекаем текст
            recognized_text = result.get("result", "")

            logger.info(f"✅ SpeechKit STT: '{recognized_text}'")
            return recognized_text

        except CircuitOpenError as e:
            logger.warning(f"⚡ SpeechKit Circuit Breaker: {e}")
            raise
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

    # Embeddings API - векторные представления текста

    async def get_embedding(self, text: str, text_type: str = "doc") -> list[float] | None:
        """
        Получить вектор эмбеддинга текста через Yandex Embeddings API.

        Args:
            text: Текст для эмбеддинга
            text_type: "doc" (документы) или "query" (запросы)

        Returns:
            list[float]: Вектор эмбеддинга или None при ошибке
        """
        if not text or not self.api_key or not self.folder_id:
            return None
        model = "text-search-query/latest" if text_type == "query" else "text-search-doc/latest"
        model_uri = f"emb://{self.folder_id}/{model}"
        payload = {"modelUri": model_uri, "text": text[:8000]}  # лимит API
        try:
            response = await self._client.post(
                self.embedding_url,
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            embedding = data.get("embedding")
            if embedding and isinstance(embedding, list):
                return [float(x) for x in embedding]
            return None
        except Exception as e:
            logger.warning(f"⚠️ Embeddings API недоступен: {e}")
            return None

    # Vision OCR - анализ изображений

    async def recognize_text(self, image_data: bytes) -> str:
        """
        Распознать текст на изображении через Vision OCR (без анализа GPT).

        Используется для модерации изображений (moderate_image_content).

        Args:
            image_data: Изображение в байтах.

        Returns:
            str: Распознанный текст или пустая строка.
        """
        try:
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

            async def _execute_request():
                response = await self._client.post(
                    self.vision_url, headers=self.headers, json=vision_payload
                )
                response.raise_for_status()
                return response.json()

            async def _cb_request():
                return await self.request_queue.process(_execute_request)

            vision_result = await yandex_vision_circuit.call(_cb_request)
            return self._extract_text_from_vision_result(vision_result)
        except Exception as e:
            logger.warning(f"⚠️ Vision OCR (recognize_text) не удалось: {e}")
            return ""

    async def analyze_image_with_text(
        self,
        image_data: bytes,
        user_question: str | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Анализ изображения: OCR + описание через YandexGPT.

        Args:
            image_data: Изображение в байтах
            user_question: Вопрос пользователя об изображении
            system_prompt: Опционально — системный промпт для стиля ответа (например, проверка ДЗ)

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
            @retry(
                stop=stop_after_attempt(2),
                wait=wait_exponential(multiplier=1, min=1, max=8),
                retry=retry_if_exception_type((httpx.TimeoutException, httpx.RequestError)),
                before_sleep=lambda rs: logger.warning(
                    f"🔄 Vision retry {rs.attempt_number}/2: {rs.outcome.exception()}"
                ),
                reraise=True,
            )
            async def _execute_request():
                response = await self._client.post(
                    self.vision_url, headers=self.headers, json=vision_payload
                )
                response.raise_for_status()
                return response.json()

            # Выполняем запрос через Circuit Breaker + очередь
            async def _cb_request():
                return await self.request_queue.process(_execute_request)

            vision_result = await yandex_vision_circuit.call(_cb_request)

            logger.debug(f"📊 Vision API response keys: {list(vision_result.keys())}")

            # Полный ответ — только DEBUG (предотвращает мегабайты логов в prod)
            response_full = json.dumps(vision_result, ensure_ascii=False, indent=2)
            logger.debug(f"📊 Vision API response:\n{response_full[:2000]}")

            recognized_text = self._extract_text_from_vision_result(vision_result)

            if recognized_text:
                logger.info(f"✅ Vision OCR: {len(recognized_text)} символов")
                logger.debug(f"📝 Первые 200 символов:\n{recognized_text[:200]}")
            else:
                logger.warning("⚠️ Vision API вернул ответ, но текст пустой!")
                logger.debug(f"⚠️ Структура ответа: {response_full[:500]}")

        except (KeyError, IndexError, AttributeError) as e:
            logger.error(f"❌ Ошибка парсинга Vision API: {type(e).__name__}: {e}")
            recognized_text = ""

        # ВАЖНО: Не обрываем процесс даже если OCR распознал мало текста!
        # YandexGPT попробует работать с тем что есть

        # Если текст совсем не распознан - даем подробный совет
        if not recognized_text:
            logger.warning("⚠️ OCR не распознал НИКАКОГО текста на изображении")
            return {
                "recognized_text": "",
                "analysis": (
                    "📷 Разбор задания:\n"
                    "📸 Я не смог распознать текст на фотографии.\n\n"
                    "💡 Совет: Лучше фотографировать БУМАГУ, а не экран!\n\n"
                    "Как сделать хорошее фото:\n"
                    "✅ При хорошем освещении\n"
                    "✅ Четко и ровно (не под углом)\n"
                    "✅ Крупным планом\n"
                    "✅ Без бликов и теней\n"
                    "✅ Текст должен быть четким\n\n"
                    "Или проще:\n"
                    "📝 Напиши задачи текстом — так будет точнее и быстрее! ✨"
                ),
                "has_text": False,
            }

        # Если текст короткий - предупреждаем, но всё равно пробуем
        if len(recognized_text) < 20:
            logger.warning(
                f"⚠️ OCR распознал мало текста ({len(recognized_text)} символов): '{recognized_text}'"
            )

        # Шаг 2: Определяем язык текста и переводим если не русский
        translated_text = recognized_text
        language_info = ""

        try:
            from bot.services.translate_service import get_translate_service

            translate_service = get_translate_service()
            detected_lang = await translate_service.detect_language(recognized_text)

            if (
                detected_lang
                and detected_lang != "ru"
                and detected_lang in translate_service.SUPPORTED_LANGUAGES
            ):
                lang_name = translate_service.get_language_name(detected_lang)
                logger.info(f"🌍 OCR: Обнаружен текст на {lang_name} ({detected_lang})")
                translated_text = await translate_service.translate_text(
                    recognized_text, target_language="ru", source_language=detected_lang
                )
                if translated_text:
                    language_info = f"\n\n🌍 ОБНАРУЖЕН ИНОСТРАННЫЙ ЯЗЫК: {lang_name}\n📝 Оригинал: {recognized_text}\n🇷🇺 Перевод: {translated_text}\n\n"
                    logger.info(f"✅ Текст переведен с {detected_lang} на русский")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка перевода OCR текста: {e}, продолжаем с оригинальным текстом")

        # Шаг 3: Решаем через YandexGPT (даже если текста мало)
        logger.info(
            f"🤖 Отправляю распознанный текст ({len(translated_text)} символов) в YandexGPT"
        )

        try:
            # ЗАКОММЕНТИРОВАНО - полная свобода для Yandex Pro 5.1
            # analysis_prompt = f"""
            # На фотографии школьное задание или учебный материал.
            #
            # {language_info}РАСПОЗНАННЫЙ ТЕКСТ с изображения (на русском):
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # {translated_text}
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            #
            # Вопрос ученика: {user_question or "Помоги решить эти задачи"}
            #
            # Если это учебный материал — РЕШАЙ задачи или объясняй тему
            #
            # 🚫 КРИТИЧЕСКИ ВАЖНО - ЧТО НЕ ДЕЛАТЬ С ФОТО:
            # ❌ НЕ говори "молодец что отправил фото" - сразу РЕШАЙ задачи!
            # ❌ НЕ хвали за отправку фото - ученик ждет РЕШЕНИЯ, а не похвалы!
            # ❌ НЕ пиши "вижу задачу" и не останавливайся - РЕШАЙ её полностью!
            # ❌ НЕ говори "Да конечно помогу пришли мне описание того что на фото" - фото УЖЕ проанализировано, РЕШАЙ задачу!
            # ❌ НЕ проси описание фото - фото УЖЕ распознано, используй текст выше!
            #
            # ✅ ТВОЯ ГЛАВНАЯ ЗАДАЧА - РЕШАТЬ ЗАДАЧИ:
            #
            # {("🌍 ОБНАРУЖЕН ИНОСТРАННЫЙ ЯЗЫК! " if language_info else "")}Если это ЗАДАЧИ/ПРИМЕРЫ/УРАВНЕНИЯ:
            #    ✅ СРАЗУ РЕШИ КАЖДУЮ задачу полностью (не просто объясни, а РЕШИ!)
            #    ✅ Дай конкретный ответ с числом/результатом
            #    {"- Если текст был на иностранном языке - объясни перевод и грамматику простыми словами" if language_info else ""}
            #
            # Если это РЕЦЕПТ/ИНСТРУКЦИЯ:
            #    ✅ Объясни простыми словами что нужно делать
            #    ✅ Разбей на понятные шаги
            #    ✅ Дай полезные советы
            #    {"- Если текст был на иностранном языке - объясни перевод и важные слова" if language_info else ""}
            #
            # Если это ПРАВИЛО/ОПРЕДЕЛЕНИЕ:
            #    ✅ Объясни своими словами
            #    ✅ Приведи простые примеры
            #    ✅ Помоги запомнить
            #    {"- Если текст был на иностранном языке - объясни перевод и грамматические правила" if language_info else ""}
            # """

            # Полная свобода для Yandex Pro 5.1 - только распознанный текст
            analysis_prompt = f"""
{language_info}РАСПОЗНАННЫЙ ТЕКСТ с изображения (на русском):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{translated_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Вопрос ученика: {user_question or "Помоги решить эти задачи"}
"""

            gpt_analysis = await self.generate_text_response(
                user_message=analysis_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
            )

            return {
                "recognized_text": recognized_text,
                "analysis": gpt_analysis,
                "has_text": bool(recognized_text),
            }

        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.RequestError) as e:
            logger.error(
                f"❌ Ошибка YandexGPT API при анализе фото (HTTP {getattr(e, 'response', None) and e.response.status_code or 'unknown'}): {e}",
                exc_info=True,
            )
            # Возвращаем явный маркер ошибки для обработки в вызывающем коде
            error_msg = "Временная проблема с AI сервисом. Попробуйте позже."
            return {
                "recognized_text": recognized_text,
                "analysis": error_msg,
                "has_text": bool(recognized_text),
            }
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при анализе фото: {e}", exc_info=True)
            error_msg = f"Не удалось проанализировать изображение: {str(e)}"
            return {
                "recognized_text": recognized_text,
                "analysis": error_msg,
                "has_text": bool(recognized_text),
            }

    # Утилиты

    def get_model_info(self) -> dict[str, str]:
        """Информация о текущей модели."""
        return {
            "provider": "Yandex Cloud",
            "model": self.gpt_model,
            "capabilities": "text, speech, vision",
            "language": "ru, en",
        }


# Глобальный экземпляр (Singleton)

_yandex_service: YandexCloudService | None = None


def get_yandex_cloud_service() -> YandexCloudService:
    """Получить глобальный экземпляр Yandex Cloud сервиса."""
    global _yandex_service
    if _yandex_service is None:
        _yandex_service = YandexCloudService()
    return _yandex_service
