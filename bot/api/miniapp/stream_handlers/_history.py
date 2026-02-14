"""Сохранение истории, геймификация и уведомления о лимитах."""

import asyncio

from aiohttp import web
from loguru import logger

from bot.api.miniapp.helpers import (
    extract_user_grade_from_message,
    extract_user_name_from_message,
    send_achievements_event,
)


async def save_and_notify(
    db,
    premium_service,
    history_service,
    telegram_id: int,
    user_message: str,
    full_response_for_db: str,
    visualization_image_base64: str | None,
    is_educational: bool,
    is_history_cleared: bool,
    user,
    response: web.StreamResponse,
    panda_reaction: str | None = None,
) -> tuple[bool, int]:
    """Сохранить в историю, проверить достижения, отправить уведомления. Возвращает (limit_reached, total_requests)."""
    limit_reached = False
    total_requests = 0

    try:
        limit_reached, total_requests = premium_service.increment_request_count(telegram_id)

        # Проактивное уведомление при достижении лимита
        if limit_reached:
            asyncio.create_task(premium_service.send_limit_reached_notification_async(telegram_id))
            limit_msg = premium_service.get_limit_reached_message_text()
            history_service.add_message(telegram_id, limit_msg, "ai")

        history_service.add_message(telegram_id, user_message, "user")

        # Формируем image_url из base64 если есть визуализация
        image_url = None
        if visualization_image_base64:
            image_url = f"data:image/png;base64,{visualization_image_base64}"
        history_service.add_message(
            telegram_id,
            full_response_for_db,
            "ai",
            image_url=image_url,
            panda_reaction=panda_reaction,
        )

        from bot.services.panda_lazy_service import PandaLazyService

        PandaLazyService(db).increment_consecutive_after_ai(telegram_id)

        if is_educational:
            from bot.services.learning_session_service import LearningSessionService

            LearningSessionService(db).record_educational_question(telegram_id)

        # Если история была очищена — пробуем извлечь имя или класс
        if is_history_cleared and not user.skip_name_asking:
            if not user.first_name:
                extracted_name, is_refusal = extract_user_name_from_message(user_message)
                if is_refusal:
                    user.skip_name_asking = True
                    logger.info(
                        "✅ Stream: Пользователь отказался называть имя, устанавливаем флаг skip_name_asking"
                    )
                elif extracted_name:
                    user.first_name = extracted_name
                    logger.info(f"✅ Stream: Имя пользователя обновлено: {user.first_name}")

            if not user.grade:
                extracted_grade = extract_user_grade_from_message(user_message)
                if extracted_grade:
                    user.grade = extracted_grade
                    logger.info(f"✅ Stream: Класс пользователя обновлен: {user.grade}")

        # Геймификация
        unlocked_achievements = []
        try:
            from bot.services.gamification_service import GamificationService

            gamification_service = GamificationService(db)
            unlocked_achievements = gamification_service.process_message(telegram_id, user_message)
        except Exception as e:
            logger.error(f"❌ Stream: Ошибка геймификации: {e}", exc_info=True)

        db.commit()

        # Отправляем информацию о достижениях
        if unlocked_achievements:
            await send_achievements_event(response, unlocked_achievements)

    except Exception as save_error:
        logger.error(f"❌ Stream: Ошибка сохранения: {save_error}", exc_info=True)
        db.rollback()

    return limit_reached, total_requests
