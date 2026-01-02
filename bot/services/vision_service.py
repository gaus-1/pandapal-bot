"""
Сервис анализа изображений через Yandex Vision OCR.

Использует Yandex Cloud Vision API для распознавания текста на изображениях.
Wrapper для совместимости с существующими handlers.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from loguru import logger

from bot.services.yandex_cloud_service import get_yandex_cloud_service


class SafetyLevel(Enum):
    """Уровень безопасности изображения."""

    SAFE = "safe"
    UNSAFE = "unsafe"
    UNKNOWN = "unknown"


@dataclass
class ImageAnalysisResult:
    """
    Результат анализа изображения через Yandex Vision OCR.
    """

    recognized_text: str
    description: str
    analysis: str
    safety_level: SafetyLevel
    has_text: bool


class VisionService:
    """
    Сервис для анализа изображений через Yandex Vision + YandexGPT.

    Возможности:
    - OCR (распознавание текста)
    - Анализ учебных заданий
    - Проверка безопасности контента
    """

    def __init__(self):
        """Инициализация сервиса."""
        self.yandex_service = get_yandex_cloud_service()
        logger.info("✅ Yandex Vision сервис инициализирован")

    async def analyze_image(
        self,
        image_data: bytes,
        user_message: Optional[str] = None,
        user_age: Optional[int] = None,
    ) -> ImageAnalysisResult:
        """
        Анализировать изображение через Yandex Vision + YandexGPT.

        Args:
            image_data: Данные изображения в байтах.
            user_message: Вопрос пользователя об изображении.
            user_age: Возраст пользователя для адаптации ответа.

        Returns:
            ImageAnalysisResult: Результат анализа.
        """
        try:
            logger.info("📷 Анализ изображения через Yandex Vision...")

            # Анализируем через Yandex Cloud
            result = await self.yandex_service.analyze_image_with_text(
                image_data=image_data, user_question=user_message
            )

            # Формируем результат в совместимом формате
            recognized_text = result.get("recognized_text", "")
            analysis = result.get("analysis", "")
            has_text = result.get("has_text", False)

            return ImageAnalysisResult(
                recognized_text=recognized_text,
                description=analysis,  # Описание = анализ от GPT
                analysis=analysis,
                safety_level=SafetyLevel.SAFE,  # Yandex Vision не блокирует контент
                has_text=has_text,
            )

        except Exception as e:
            logger.error(f"❌ Ошибка анализа изображения (Yandex): {e}")
            return ImageAnalysisResult(
                recognized_text="",
                description="Ошибка анализа",
                analysis="Не удалось проанализировать изображение",
                safety_level=SafetyLevel.UNKNOWN,
                has_text=False,
            )

    async def generate_educational_response(
        self,
        analysis_result: ImageAnalysisResult,
        user_message: Optional[str] = None,
        user_age: Optional[int] = None,
    ) -> str:
        """
        Генерировать образовательный ответ на основе анализа изображения.

        Args:
            analysis_result: Результат анализа изображения.
            user_message: Сопровождающий текст пользователя.
            user_age: Возраст пользователя.

        Returns:
            str: Образовательный ответ.
        """
        try:
            # Yandex Vision уже генерирует образовательный ответ
            # Просто форматируем его красиво
            response_parts = []

            if analysis_result.recognized_text:
                response_parts.append(
                    f"📝 <b>Текст на изображении:</b>\n{analysis_result.recognized_text}\n"
                )

            if analysis_result.analysis:
                response_parts.append(f"🎓 <b>Разбор задания:</b>\n{analysis_result.analysis}")

            if not response_parts:
                return (
                    "📷 Я не смог распознать текст на изображении.\n\n"
                    "Попробуй сфотографировать задание более четко! 📝"
                )

            return "\n".join(response_parts)

        except Exception as e:
            logger.error(f"❌ Ошибка генерации образовательного ответа: {e}")
            return "😔 Извини, у меня возникли проблемы. Попробуй ещё раз!"
