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

            # Сохраняем в историю (синхронный метод, без await)
            history_service.add_message(
                telegram_id=message.from_user.id,
                message_text=f"[ИЗОБРАЖЕНИЕ] {caption}" if caption else "[ИЗОБРАЖЕНИЕ]",
                message_type="user",
            )

            history_service.add_message(
                telegram_id=message.from_user.id, message_text=ai_response, message_type="ai"
            )

            # Проверяем, нужна ли визуализация в ответе AI
            visualization_image = None
            try:
                from bot.services.visualization_service import get_visualization_service

                viz_service = get_visualization_service()
                # Используем универсальный метод детекции для ответа AI
                visualization_image, _ = viz_service.detect_visualization_request(ai_response)
            except Exception as e:
                logger.debug(f"⚠️ Ошибка генерации визуализации для фото: {e}")

            # Отправляем ответ с визуализацией если есть
            if visualization_image:
                from aiogram.types import BufferedInputFile

                photo = BufferedInputFile(visualization_image, filename="visualization.png")
                await processing_msg.delete()
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
