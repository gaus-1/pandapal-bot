"""
Обработка изображений для AI чата.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, PhotoSize
from loguru import logger

from bot.database import get_db
from bot.monitoring import log_user_activity, monitor_performance
from bot.services import ChatHistoryService, UserService
from bot.services.ai_service_solid import get_ai_service

from .helpers import read_file_safely


def register_handlers(router: Router) -> None:
    """Регистрирует handlers для изображений."""
    router.message.register(handle_image, F.photo)


@monitor_performance
async def handle_image(message: Message, state: FSMContext):  # noqa: ARG001
    """
    Обработка изображений через AI Vision

    ВАЖНО: Полный цикл обработки изображений с модерацией.
    Использует Yandex Vision OCR для извлечения текста и анализа содержимого.
    Включает проверку безопасности контента на изображении.

    Args:
        message: Сообщение с изображением
        state: FSM состояние
    """
    try:
        # Получаем самое большое изображение
        photo: PhotoSize = max(message.photo, key=lambda p: p.file_size)

        # Проверяем размер изображения
        if photo.file_size > 20 * 1024 * 1024:  # 20MB лимит
            await message.answer(
                "🖼️ Изображение слишком большое! Максимум 20MB. "
                "Попробуй сжать фото и отправить снова 📏"
            )
            return

        # Показываем, что обрабатываем изображение
        processing_msg = await message.answer("🖼️ Анализирую изображение... Пожалуйста, подожди! 🐼")

        # Получаем файл изображения
        file = await message.bot.get_file(photo.file_id)
        image_data = await message.bot.download_file(file.file_path)

        # Читаем данные изображения потоково с ограничением размера
        max_image_size = 20 * 1024 * 1024  # 20MB лимит (уже проверено выше, но для безопасности)
        try:
            image_bytes = read_file_safely(image_data, max_size=max_image_size)
        except ValueError as e:
            logger.warning(f"⚠️ Изображение превышает лимит: {e}")
            await processing_msg.edit_text(
                "🖼️ Изображение слишком большое! " "Попробуй сжать фото и отправить снова 📏"
            )
            return

        # Получаем пользователя и его данные
        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(message.from_user.id)

            if not user:
                await processing_msg.edit_text("❌ Сначала зарегистрируйся командой /start")
                return

            # КРИТИЧНО: Проверка Premium для неограниченных запросов
            from bot.services.premium_features_service import PremiumFeaturesService

            premium_service = PremiumFeaturesService(db)
            can_request, limit_reason = premium_service.can_make_ai_request(
                message.from_user.id, username=message.from_user.username
            )

            if not can_request:
                logger.warning(
                    f"🚫 AI запрос (изображение) заблокирован для user={message.from_user.id}: {limit_reason}"
                )
                from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="💎 Узнать о Premium", callback_data="premium:info"
                            )
                        ]
                    ]
                )

                await processing_msg.edit_text(
                    limit_reason, reply_markup=keyboard, parse_mode="HTML"
                )
                return

            # Получаем сервисы
            ai_service = get_ai_service()
            history_service = ChatHistoryService(db)

            # Проверяем модерацию изображения
            is_safe, reason = await ai_service.moderate_image_content(image_bytes)

            if not is_safe:
                await processing_msg.edit_text(
                    "🚫 Это изображение не подходит для детей. "
                    "Попробуй отправить что-то другое! 🐼"
                )
                log_user_activity(message.from_user.id, "image_blocked", False, reason)
                return

            # Получаем подпись к изображению (если есть)
            caption = message.caption or ""

            # Анализируем изображение с помощью AI
            ai_response = await ai_service.analyze_image(
                image_data=image_bytes,
                user_message=caption,
                user_age=user.age,
            )

            # Проверяем ответ AI на запрещенные темы (дополнительная проверка)
            from bot.services.moderation_service import ContentModerationService

            moderation_service = ContentModerationService()
            is_safe_response, reason = moderation_service.is_safe_content(ai_response)

            if not is_safe_response:
                # Вежливо переводим на учебу, не упоминая запрещенную тему
                await processing_msg.edit_text(
                    "🚫 Это изображение не подходит для учебы. "
                    "Попробуй отправить фото с задачей или вопросом по школьным предметам! "
                    "Я помогу с математикой, русским, историей, географией и другими предметами! 🐼📚"
                )
                log_user_activity(message.from_user.id, "image_blocked_ai_response", False, reason)
                return

            # Увеличиваем счетчик запросов (независимо от истории)
            limit_reached, total_requests = premium_service.increment_request_count(
                message.from_user.id
            )

            # Проактивное уведомление от панды при достижении лимита
            if limit_reached:
                try:
                    from aiogram import Bot

                    from bot.config import settings

                    bot_instance = Bot(token=settings.telegram_bot_token)
                    await premium_service.send_limit_reached_notification(
                        message.from_user.id, bot_instance
                    )
                    await bot_instance.session.close()
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки проактивного уведомления: {e}")

            # Сохраняем в историю (синхронный метод, без await)
            history_service.add_message(
                telegram_id=message.from_user.id,
                message_text=f"[ИЗОБРАЖЕНИЕ] {caption}" if caption else "[ИЗОБРАЖЕНИЕ]",
                message_type="user",
            )

            history_service.add_message(
                telegram_id=message.from_user.id, message_text=ai_response, message_type="ai"
            )

            # Проверяем, нужна ли визуализация в ответе AI (из caption или из ответа)
            visualization_image = None
            visualization_type = None
            try:
                from bot.services.visualization_service import get_visualization_service

                viz_service = get_visualization_service()
                # Проверяем caption (если есть) - там может быть запрос на визуализацию
                if caption:
                    visualization_image, visualization_type = (
                        viz_service.detect_visualization_request(caption)
                    )
                # Если в caption не найдено, проверяем ответ AI
                if not visualization_image:
                    visualization_image, visualization_type = (
                        viz_service.detect_visualization_request(ai_response)
                    )
            except Exception as e:
                logger.debug(f"⚠️ Ошибка генерации визуализации для фото: {e}")

            # Удаляем упоминания про автоматическую генерацию из ответа
            if visualization_image:
                import re

                patterns_to_remove = [
                    r"(?:систем[аеы]?\s+)?автоматически\s+сгенериру[ею]т?\s+(?:изображени[ея]?|график|таблиц[ау]|карт[ау]|диаграмм[ау]|схем[ау]|визуализаци[юя])",
                    r"покажу\s+(?:график|таблиц[ау]|карт[ау]|диаграмм[ау]|схем[ау]).*?систем[аеы]?\s+автоматически",
                    r"автоматически\s+создан[аоы]?\s+(?:график|таблиц[ау]|карт[ау]|диаграмм[ау]|схем[ау]|визуализаци[юя])",
                    r"создан[аоы]?\s+автоматически\s+(?:график|таблиц[ау]|карт[ау]|диаграмм[ау]|схем[ау]|визуализаци[юя])",
                    r"генерируется\s+автоматически",
                    r"автоматическая\s+генерация",
                    r"сгенерирован[аоы]?\s+автоматически",
                    r"\[Сгенерирован[аоы]?\s+(?:карт[ау]|график|таблиц[ау]|диаграмм[ау]|схем[ау])\]",
                    r"Сгенерирован[аоы]?\s+(?:карт[ау]|график|таблиц[ау]|диаграмм[ау]|схем[ау])",
                    r"Эта\s+(?:карт[ау]|график|таблиц[ау]|диаграмм[ау]|схем[ау])\s+был[аоы]?\s+создан[аоы]?\s+автоматически",
                    r"Эта\s+(?:карт[ау]|график|таблиц[ау]|диаграмм[ау]|схем[ау])\s+был[аоы]?\s+сгенерирован[аоы]?\s+автоматически",
                    r"автоматически\s+владельцем\s+сайт[аа]?",
                    r"автоматически\s+на\s+основе",
                    r"создан[аоы]?\s+автоматически\s+владельцем",
                    r"сгенерирован[аоы]?\s+автоматически\s+владельцем",
                    r"Эта\s+карт[ау]\s+был[аоы]?\s+создан[аоы]?\s+автоматически\s+владельцем\s+сайт[аа]?\s+на\s+основе",
                    r"карт[ау]\s+создан[аоы]?\s+автоматически",
                    r"карт[ау]\s+сгенерирован[аоы]?\s+автоматически",
                ]
                for pattern in patterns_to_remove:
                    ai_response = re.sub(pattern, "", ai_response, flags=re.IGNORECASE)
                ai_response = re.sub(r"\s+", " ", ai_response)
                ai_response = re.sub(r"\n\s*\n", "\n", ai_response)
                ai_response = ai_response.strip()

            # Отправляем ответ с визуализацией если есть
            if visualization_image:
                from aiogram.types import BufferedInputFile

                photo = BufferedInputFile(visualization_image, filename="visualization.png")
                await processing_msg.delete()
                # Отправляем визуализацию с подробным описанием
                await message.answer_photo(
                    photo=photo,
                    caption=ai_response[:1024],  # Telegram ограничение на caption
                )
                # Если текст длиннее, отправляем остаток отдельным сообщением
                if len(ai_response) > 1024:
                    await message.answer(text=ai_response[1024:])
            else:
                await processing_msg.edit_text(ai_response)

            log_user_activity(
                message.from_user.id, "image_analyzed", True, f"Size: {len(image_bytes)} bytes"
            )

    except Exception as e:
        logger.error(f"❌ Ошибка обработки изображения: {e}")
        await message.answer(
            "🖼️ Произошла ошибка при анализе изображения. " "Попробуй отправить другое фото! 🐼"
        )
        log_user_activity(message.from_user.id, "image_error", False, str(e))
