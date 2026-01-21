"""
Сервис для обработки фото в Mini App.

Отвечает за:
- Анализ изображения через Vision API
- Обработку готовых ответов от Vision
- Сохранение в историю и геймификацию
- Валидацию размера фото
"""

import base64
import json

from aiohttp import web
from loguru import logger

from bot.api.miniapp.helpers import send_achievements_event
from bot.database import get_db
from bot.services import ChatHistoryService, UserService
from bot.services.gamification_service import GamificationService
from bot.services.premium_features_service import PremiumFeaturesService
from bot.services.vision_service import VisionService
from bot.services.yandex_ai_response_generator import clean_ai_response


class MiniappPhotoService:
    """Сервис для обработки фотографий в Mini App."""

    def __init__(self):
        """Инициализация сервиса."""
        self.vision_service = VisionService()

    async def process_photo(
        self,
        photo_base64: str,
        telegram_id: int,
        message: str,
        response: web.StreamResponse,
    ) -> tuple[str | None, bool]:
        """
        Обрабатывает фотографию.

        Args:
            photo_base64: Base64 строка изображения (может содержать префикс data:image/...;base64,)
            telegram_id: ID пользователя в Telegram
            message: Текстовое сообщение пользователя (опционально)
            response: SSE response для отправки событий

        Returns:
            Tuple[Optional[str], bool]: (user_message, is_completed)
            - user_message: Текст для дальнейшей обработки или None при ошибке
            - is_completed: True если ответ уже отправлен (Vision дал готовый ответ), False если нужна дальнейшая обработка
        """
        try:
            logger.info(f"📷 Stream: Обработка фото от {telegram_id}")

            # Отправляем событие обработки фото
            await response.write(b'event: status\ndata: {"status": "analyzing_photo"}\n\n')

            # Убираем data:image/...;base64, префикс
            if "base64," in photo_base64:
                photo_base64 = photo_base64.split("base64,")[1]

            photo_bytes = base64.b64decode(photo_base64)

            with get_db() as db:
                user_service = UserService(db)
                user = user_service.get_user_by_telegram_id(telegram_id)

                if not user:
                    await response.write(b'event: error\ndata: {"error": "User not found"}\n\n')
                    return None, True

                # Анализ изображения через Vision API
                vision_result = await self.vision_service.analyze_image(
                    image_data=photo_bytes,
                    user_message=message
                    or "Проанализируй это фото с заданием и реши задачу полностью",
                    user_age=user.age,
                )

                logger.info("✅ Stream: Фото проанализировано")
                await response.write(b'event: status\ndata: {"status": "photo_analyzed"}\n\n')

                # Проверяем, что анализ не является сообщением об ошибке
                is_error_message = vision_result.analysis and (
                    "Не удалось проанализировать" in vision_result.analysis
                    or "Временная проблема с AI сервисом" in vision_result.analysis
                    or "Ошибка анализа" in vision_result.analysis
                )

                # КРИТИЧЕСКИ ВАЖНО: Если Vision API дал готовый ответ - сразу отправляем его!
                if (
                    vision_result.analysis
                    and vision_result.analysis.strip()
                    and not is_error_message
                ):
                    # Vision API уже решил задачу - отправляем ответ напрямую
                    full_response = clean_ai_response(vision_result.analysis)

                    # КРИТИЧНО: Проверка ответа Vision API на запрещенные темы
                    from bot.services.moderation_service import ContentModerationService

                    moderation_service = ContentModerationService()
                    is_safe_response, reason = moderation_service.is_safe_content(full_response)
                    if not is_safe_response:
                        logger.warning(
                            f"🚫 Stream: Vision API вернул небезопасный ответ для фото от {telegram_id}: {reason}"
                        )
                        # Заменяем на безопасный ответ
                        full_response = moderation_service.get_safe_response_alternative()

                    # Отправляем ответ через streaming
                    chunk_data = json.dumps({"chunk": full_response}, ensure_ascii=False)
                    await response.write(f"event: chunk\ndata: {chunk_data}\n\n".encode())

                    # Сохраняем в историю
                    try:
                        premium_service = PremiumFeaturesService(db)
                        history_service = ChatHistoryService(db)

                        limit_reached, total_requests = premium_service.increment_request_count(
                            telegram_id
                        )

                        # Проактивное уведомление от панды при достижении лимита (фоновая задача)
                        if limit_reached:
                            import asyncio

                            asyncio.create_task(
                                premium_service.send_limit_reached_notification_async(telegram_id)
                            )
                        user_msg_text = message or "📷 Фото"
                        history_service.add_message(telegram_id, user_msg_text, "user")
                        history_service.add_message(telegram_id, full_response, "ai")

                        # Геймификация
                        unlocked_achievements = []
                        try:
                            gamification_service = GamificationService(db)
                            unlocked_achievements = gamification_service.process_message(
                                telegram_id, user_msg_text
                            )
                        except Exception as e:
                            logger.error(f"❌ Stream: Ошибка геймификации: {e}", exc_info=True)

                        db.commit()

                        # Отправляем информацию о достижениях если есть
                        if unlocked_achievements:
                            await send_achievements_event(response, unlocked_achievements)
                    except Exception as save_error:
                        logger.error(f"❌ Stream: Ошибка сохранения: {save_error}", exc_info=True)
                        db.rollback()

                    # Отправляем событие завершения
                    await response.write(b'event: done\ndata: {"status": "completed"}\n\n')
                    logger.info(f"✅ Stream: Фото ответ отправлен напрямую для {telegram_id}")
                    return None, True

                # Если Vision API вернул ошибку - отправляем ошибку пользователю
                if is_error_message:
                    logger.error(f"❌ Stream: Vision API вернул ошибку для фото от {telegram_id}")
                    error_msg = 'event: error\ndata: {"error": "Временная проблема с AI сервисом. Попробуйте позже."}\n\n'
                    await response.write(error_msg.encode("utf-8"))
                    return None, True

                # Если Vision API не дал готовый ответ - используем распознанный текст
                if vision_result.recognized_text:
                    # КРИТИЧНО: Проверка распознанного текста на запрещенные темы
                    from bot.services.moderation_service import ContentModerationService

                    moderation_service = ContentModerationService()
                    is_safe, reason = moderation_service.is_safe_content(
                        vision_result.recognized_text
                    )
                    if not is_safe:
                        logger.warning(
                            f"🚫 Stream: Запрещенная тема в распознанном тексте фото от {telegram_id}: {reason}"
                        )
                        # Вежливо перенаправляем на учебу
                        safe_response = moderation_service.get_safe_response_alternative()
                        await response.write(
                            f'event: message\ndata: {{"content": {json.dumps(safe_response, ensure_ascii=False)}}}\n\n'.encode()
                        )
                        await response.write(b"event: done\ndata: {}\n\n")
                        return None, True

                    user_message = (
                        f"На фото написано: {vision_result.recognized_text}\n\n"
                        "Помоги решить эту задачу полностью."
                    )
                else:
                    user_message = message or "Помоги мне разобраться с этой задачей"

                return user_message, False

        except Exception as e:
            logger.error(f"❌ Stream: Ошибка обработки фото: {e}", exc_info=True)
            await response.write(
                f'event: error\ndata: {{"error": "Ошибка обработки фото: {str(e)}"}}\n\n'.encode()
            )
            return None, True
