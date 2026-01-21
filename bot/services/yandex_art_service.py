"""
Сервис генерации изображений через YandexART.

Yandex Foundation Models (YandexART) - генеративная модель для создания изображений.
API Documentation: https://yandex.cloud/ru/docs/foundation-models/image-generation/api-ref/

Требования:
- Роль ai.imageGeneration.user в Yandex Cloud (см. скриншот)
- API key с правами на генерацию изображений
- Folder ID проекта в Yandex Cloud
"""

import asyncio
import base64
from typing import Literal

import httpx
from loguru import logger

from bot.config import settings


class YandexARTService:
    """
    Сервис для генерации изображений через YandexART.

    Основные возможности:
    - Генерация изображений по текстовому описанию
    - Поддержка разных стилей (реалистичный, аниме, комиксы и т.д.)
    - Асинхронная генерация с polling результата
    - Автоматическая обработка ошибок и повторные попытки
    """

    def __init__(self):
        """Инициализация сервиса YandexART."""
        self.api_key = settings.yandex_cloud_api_key
        self.folder_id = settings.yandex_cloud_folder_id
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1"
        self.timeout = httpx.Timeout(60.0, connect=10.0)

        # Модели YandexART
        self.model_uri = f"art://{self.folder_id}/yandex-art/latest"

        logger.info("🎨 YandexARTService инициализирован")

    async def generate_image(
        self,
        prompt: str,
        style: Literal["auto", "anime", "realism", "comics", "oil", "watercolor"] = "auto",
        aspect_ratio: Literal["1:1", "16:9", "9:16", "4:3", "3:4"] = "1:1",
        timeout: int = 120,
    ) -> bytes | None:
        """
        Генерирует изображение по текстовому описанию.

        Args:
            prompt: Текстовое описание изображения на русском
            style: Стиль изображения (auto, anime, realism, comics, oil, watercolor)
            aspect_ratio: Соотношение сторон изображения
            timeout: Максимальное время ожидания генерации (секунды)

        Returns:
            bytes: Изображение в формате PNG или None при ошибке

        Example:
            >>> service = YandexARTService()
            >>> image_bytes = await service.generate_image(
            ...     "Милая панда читает книгу в библиотеке",
            ...     style="anime"
            ... )
        """
        try:
            # 1. Отправляем запрос на генерацию
            operation_id = await self._submit_generation_request(prompt, style, aspect_ratio)
            if not operation_id:
                return None

            # 2. Ждём завершения генерации (polling)
            image_base64 = await self._poll_generation_result(operation_id, timeout=timeout)
            if not image_base64:
                return None

            # 3. Декодируем base64 в bytes
            image_bytes = base64.b64decode(image_base64)
            logger.info(f"✅ Изображение сгенерировано: {len(image_bytes)} bytes, стиль={style}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации изображения: {e}", exc_info=True)
            return None

    async def _submit_generation_request(
        self, prompt: str, style: str, aspect_ratio: str
    ) -> str | None:
        """
        Отправляет запрос на генерацию изображения.

        Args:
            prompt: Текстовое описание
            style: Стиль изображения
            aspect_ratio: Соотношение сторон

        Returns:
            str: Operation ID для polling или None при ошибке
        """
        url = f"{self.base_url}/imageGenerationAsync"

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "modelUri": self.model_uri,
            "generationOptions": {
                "mimeType": "image/png",
                "seed": None,  # Случайный seed для разнообразия
                "aspectRatio": {
                    "widthRatio": aspect_ratio.split(":")[0],
                    "heightRatio": aspect_ratio.split(":")[1],
                },
            },
            "messages": [
                {
                    "weight": 1,
                    "text": prompt,
                }
            ],
        }

        # Добавляем стиль, если указан (не auto)
        if style != "auto":
            style_prompts = {
                "anime": "в стиле аниме, яркие цвета, выразительные глаза, японская анимация",
                "realism": "фотореалистичный стиль, детализация, реалистичное освещение",
                "comics": "в стиле комиксов, яркие контуры, динамичная композиция",
                "oil": "в стиле масляной живописи, мазки кистью, насыщенные цвета",
                "watercolor": "акварельный стиль, мягкие переходы, прозрачные тона",
            }
            style_suffix = style_prompts.get(style, "")
            if style_suffix:
                payload["messages"][0]["text"] = f"{prompt}, {style_suffix}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                data = response.json()
                operation_id = data.get("id")

                if not operation_id:
                    logger.error(f"❌ Не получен operation_id: {data}")
                    return None

                logger.info(f"✅ Запрос на генерацию отправлен: operation_id={operation_id}")
                return operation_id

        except httpx.HTTPStatusError as e:
            logger.error(
                f"❌ HTTP ошибка при отправке запроса: {e.response.status_code} {e.response.text}"
            )
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка отправки запроса на генерацию: {e}", exc_info=True)
            return None

    async def _poll_generation_result(self, operation_id: str, timeout: int = 120) -> str | None:
        """
        Опрашивает статус генерации до получения результата.

        Args:
            operation_id: ID операции генерации
            timeout: Максимальное время ожидания (секунды)

        Returns:
            str: Base64-encoded изображение или None при ошибке
        """
        url = f"https://llm.api.cloud.yandex.net:443/operations/{operation_id}"

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
        }

        start_time = asyncio.get_event_loop().time()
        poll_interval = 2  # Опрашиваем каждые 2 секунды

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
                while True:
                    # Проверяем таймаут
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        logger.error(f"❌ Таймаут ожидания генерации: {timeout}s")
                        return None

                    # Запрашиваем статус
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()

                    data = response.json()
                    done = data.get("done", False)

                    if done:
                        # Проверяем наличие ошибки
                        if "error" in data:
                            error_message = data["error"].get("message", "Unknown error")
                            logger.error(f"❌ Ошибка генерации: {error_message}")
                            return None

                        # Извлекаем результат
                        response_data = data.get("response", {})
                        image_base64 = response_data.get("image")

                        if not image_base64:
                            logger.error(f"❌ Изображение не найдено в ответе: {data}")
                            return None

                        logger.info(f"✅ Генерация завершена за {elapsed:.1f}s")
                        return image_base64

                    # Ждём перед следующим опросом
                    logger.debug(f"⏳ Генерация в процессе... ({elapsed:.1f}s)")
                    await asyncio.sleep(poll_interval)

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP ошибка при polling: {e.response.status_code} {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка polling результата: {e}", exc_info=True)
            return None

    def is_available(self) -> bool:
        """
        Проверяет, доступен ли сервис YandexART.

        Returns:
            bool: True если API key и folder_id настроены
        """
        return bool(self.api_key and self.folder_id)


# Singleton instance
_yandex_art_service: YandexARTService | None = None


def get_yandex_art_service() -> YandexARTService:
    """
    Получить экземпляр YandexARTService (singleton).

    Returns:
        YandexARTService: Экземпляр сервиса
    """
    global _yandex_art_service
    if _yandex_art_service is None:
        _yandex_art_service = YandexARTService()
    return _yandex_art_service
