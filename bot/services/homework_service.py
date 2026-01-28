"""
Сервис проверки домашних заданий для PandaPal Bot.

Реализует проверку ДЗ через фото с сохранением результатов в БД.
"""

from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from bot.models import HomeworkSubmission
from bot.services.vision_service import VisionService


class HomeworkService:
    """Сервис проверки домашних заданий"""

    def __init__(self, db: Session):
        """
        Инициализация сервиса.

        Args:
            db: Сессия SQLAlchemy
        """
        self.db = db
        self.vision_service = VisionService()

    async def check_homework_from_photo(
        self,
        telegram_id: int,
        image_data: bytes,
        photo_file_id: str | None = None,
        photo_url: str | None = None,
        subject: str | None = None,
        topic: str | None = None,
        user_message: str | None = None,
        user_age: int | None = None,
    ) -> HomeworkSubmission:
        """
        Проверить домашнее задание по фото.

        Args:
            telegram_id: Telegram ID пользователя
            image_data: Данные изображения в байтах
            photo_file_id: Telegram file_id фотографии
            photo_url: URL фотографии (если есть)
            subject: Предмет (если известен)
            topic: Тема (если известна)
            user_message: Вопрос пользователя
            user_age: Возраст пользователя

        Returns:
            HomeworkSubmission: Результат проверки ДЗ
        """
        try:
            logger.info(f"📝 Проверка ДЗ для user={telegram_id}")

            # Проверяем через VisionService
            result = await self.vision_service.check_homework(
                image_data=image_data,
                user_message=user_message,
                user_age=user_age,
            )

            # Анализируем результат для определения ошибок
            has_errors = self._detect_errors_in_feedback(result.analysis)
            errors_found = self._extract_errors(result.analysis) if has_errors else []

            # Создаем запись о проверке ДЗ
            submission = HomeworkSubmission(
                user_telegram_id=telegram_id,
                photo_file_id=photo_file_id,
                photo_url=photo_url,
                subject=subject,
                topic=topic,
                original_text=result.recognized_text,
                ai_feedback=result.analysis,
                has_errors=has_errors,
                errors_found={"errors": errors_found} if errors_found else None,
                submitted_at=datetime.now(UTC),
            )

            self.db.add(submission)
            self.db.flush()

            logger.info(
                f"✅ ДЗ проверено: user={telegram_id}, has_errors={has_errors}, "
                f"errors_count={len(errors_found)}"
            )

            return submission

        except Exception as e:
            logger.error(f"❌ Ошибка проверки ДЗ: {e}", exc_info=True)
            raise

    def _detect_errors_in_feedback(self, feedback: str) -> bool:
        """
        Определить наличие ошибок в фидбеке AI.

        Args:
            feedback: Текст фидбека от AI

        Returns:
            bool: True если найдены ошибки
        """
        if not feedback:
            return False

        feedback_lower = feedback.lower()

        # Ключевые слова, указывающие на ошибки
        error_indicators = [
            "ошибка",
            "неправильно",
            "неверно",
            "исправь",
            "не так",
            "нужно исправить",
            "правильно было бы",
            "должно быть",
        ]

        # Ключевые слова, указывающие на правильность
        correct_indicators = [
            "правильно",
            "верно",
            "всё верно",
            "отлично",
            "молодец",
            "всё правильно",
            "нет ошибок",
        ]

        # Проверяем наличие индикаторов ошибок
        has_error_keywords = any(indicator in feedback_lower for indicator in error_indicators)
        has_correct_keywords = any(indicator in feedback_lower for indicator in correct_indicators)

        # Если есть явные индикаторы ошибок и нет индикаторов правильности
        if has_error_keywords and not has_correct_keywords:
            return True

        # Если явно указано, что всё правильно
        if has_correct_keywords and "нет ошибок" in feedback_lower:
            return False

        # По умолчанию считаем, что могут быть ошибки, если есть упоминание об исправлении
        return "исправь" in feedback_lower or "должно быть" in feedback_lower

    def _extract_errors(self, feedback: str) -> list[dict]:
        """
        Извлечь список ошибок из фидбека (базовая реализация).

        Args:
            feedback: Текст фидбека от AI

        Returns:
            List[Dict]: Список ошибок с описанием
        """
        # Базовая реализация - можно улучшить с помощью NLP
        errors = []

        if not feedback:
            return errors

        # Разбиваем на предложения и ищем упоминания ошибок
        sentences = feedback.split(". ")

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(
                word in sentence_lower
                for word in ["ошибка", "неправильно", "неверно", "исправь", "должно быть"]
            ):
                errors.append({"description": sentence.strip(), "type": "general"})

        return errors[:5]  # Ограничиваем 5 ошибками

    def get_homework_history(
        self, telegram_id: int, limit: int = 20, subject: str | None = None
    ) -> list[HomeworkSubmission]:
        """
        Получить историю проверок ДЗ для пользователя.

        Args:
            telegram_id: Telegram ID пользователя
            limit: Максимальное количество записей
            subject: Фильтр по предмету (опционально)

        Returns:
            List[HomeworkSubmission]: Список проверок ДЗ
        """
        stmt = (
            select(HomeworkSubmission)
            .where(HomeworkSubmission.user_telegram_id == telegram_id)
            .order_by(desc(HomeworkSubmission.submitted_at))
            .limit(limit)
        )

        if subject:
            stmt = stmt.where(HomeworkSubmission.subject == subject)

        return list(self.db.scalars(stmt).all())

    def get_statistics(self, telegram_id: int) -> dict:
        """
        Получить статистику проверок ДЗ для пользователя.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Dict: Статистика (всего проверок, с ошибками, без ошибок, проценты)
        """
        stmt = select(HomeworkSubmission).where(HomeworkSubmission.user_telegram_id == telegram_id)
        all_submissions = list(self.db.scalars(stmt).all())

        total = len(all_submissions)
        with_errors = sum(1 for s in all_submissions if s.has_errors)
        without_errors = total - with_errors

        error_rate = (with_errors / total * 100) if total > 0 else 0.0

        return {
            "total_checks": total,
            "with_errors": with_errors,
            "without_errors": without_errors,
            "error_rate": round(error_rate, 1),
        }
