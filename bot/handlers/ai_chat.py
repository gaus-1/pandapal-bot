"""
Обработчик общения с AI
Главная функция бота — диалог с PandaPalAI
Поддерживает текстовые сообщения и изображения

"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, PhotoSize
from loguru import logger

from bot.database import get_db
from bot.monitoring import log_user_activity, monitor_performance
from bot.services import (
    ChatHistoryService,
    ContentModerationService,
    GeminiAIService,
    UserService,
)
from bot.services.advanced_moderation import ModerationResult
from bot.services.parental_control import ActivityType, ParentalControlService

# Создаём роутер для AI чата
router = Router(name="ai_chat")


@router.message(F.text & (F.text == "💬 Общение с AI"))
@monitor_performance
async def start_ai_chat(message: Message, state: FSMContext):
    """
    Активация режима общения с AI

    Args:
        message: Сообщение от пользователя
        state: FSM состояние
    """
    await message.answer(
        text="🐼 <b>Режим общения с AI активирован!</b>\n\n"
        "Теперь просто пиши мне любые вопросы — я отвечу!\n\n"
        "Я помню наши последние 50 сообщений, так что можешь "
        "задавать уточняющие вопросы 💡",
        parse_mode="HTML",
    )


@router.message(F.text)
@monitor_performance
async def handle_ai_message(message: Message, state: FSMContext):
    """
    Обработка текстового сообщения для AI

    Алгоритм:
    1. Получить пользователя из БД
    2. Загрузить последние 50 сообщений (контекст для AI)
    3. Проверить контент на безопасность (модерация)
    4. Отправить в Gemini AI с контекстом
    5. Получить ответ
    6. Промодерировать ответ AI
    7. Сохранить оба сообщения в историю
    8. Отправить ответ пользователю

    Args:
        message: Текстовое сообщение от пользователя
        state: FSM состояние
    """
    telegram_id = message.from_user.id
    user_message = message.text

    # Показываем индикатор "печатает..."
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        # Продвинутая проверка контента на безопасность
        moderation_service = ContentModerationService()

        # Сначала базовая проверка
        is_safe, reason = moderation_service.is_safe_content(user_message)

        if not is_safe:
            logger.warning(f"🚫 Заблокирован контент от {telegram_id}: {reason}")
            moderation_service.log_blocked_content(telegram_id, user_message, reason)
            log_user_activity(telegram_id, "blocked_content", False, reason)

            safe_response = moderation_service.get_safe_response_alternative("blocked_content")
            await message.answer(text=safe_response)
            return

        # Затем продвинутая модерация
        user_context = {
            "telegram_id": telegram_id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
        }

        try:
            advanced_result = await moderation_service.advanced_moderate_content(
                user_message, user_context
            )

            # Если продвинутая модерация заблокировала контент
            if not advanced_result.is_safe:
                logger.warning(
                    f"🚫 Продвинутая модерация заблокировала контент от {telegram_id}: "
                    f"{advanced_result.reason} (уверенность: {advanced_result.confidence:.2f})"
                )

                # Логируем активность
                log_user_activity(
                    telegram_id,
                    "advanced_blocked_content",
                    False,
                    f"{advanced_result.category.value if advanced_result.category else 'unknown'}: {advanced_result.reason}",
                )

                # Записываем заблокированную активность в родительский контроль
                try:
                    with get_db() as db:
                        user_service = UserService(db)
                        user = user_service.get_user_by_telegram_id(telegram_id)

                        if user and user.user_type == "child":
                            parental_service = ParentalControlService(db)
                            await parental_service.record_child_activity(
                                child_telegram_id=telegram_id,
                                activity_type=ActivityType.MESSAGE_BLOCKED,
                                details={
                                    "category": (
                                        advanced_result.category.value
                                        if advanced_result.category
                                        else "unknown"
                                    ),
                                    "confidence": advanced_result.confidence,
                                    "reason": advanced_result.reason,
                                },
                                message_content=user_message,
                                moderation_result={
                                    "level": advanced_result.level.value,
                                    "category": (
                                        advanced_result.category.value
                                        if advanced_result.category
                                        else None
                                    ),
                                    "confidence": advanced_result.confidence,
                                },
                            )
                except Exception as e:
                    logger.error(f"❌ Ошибка записи заблокированной активности: {e}")

                # Используем альтернативный ответ из продвинутой модерации
                response_text = (
                    advanced_result.alternative_response
                    or moderation_service.get_safe_response_alternative("blocked_content")
                )
                await message.answer(text=response_text)
                return

        except Exception as e:
            logger.error(f"❌ Ошибка продвинутой модерации: {e}")
            # Продолжаем с базовой модерацией в случае ошибки

        # Работа с базой данных
        with get_db() as db:
            # Инициализируем сервисы
            user_service = UserService(db)
            history_service = ChatHistoryService(db)

            # Получаем пользователя
            user = user_service.get_or_create_user(
                telegram_id=telegram_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )

            # Загружаем последние 50 сообщений для контекста
            history = history_service.get_formatted_history_for_ai(telegram_id)

            logger.info(
                f"💬 Сообщение от {telegram_id} ({user.first_name}): "
                f"{user_message[:50]}... | История: {len(history)} сообщений"
            )

            # Инициализируем AI сервис
            ai_service = GeminiAIService()

            # Генерируем ответ с учётом контекста, возраста и класса
            ai_response = await ai_service.generate_response(
                user_message=user_message,
                chat_history=history,
                user_age=user.age,
                user_grade=user.grade,
            )

            # Промодерируем ответ AI на безопасность
            ai_response = moderation_service.sanitize_ai_response(ai_response)

            # Сохраняем сообщение пользователя в историю
            history_service.add_message(
                telegram_id=telegram_id, message_text=user_message, message_type="user"
            )

            # Сохраняем ответ AI в историю
            history_service.add_message(
                telegram_id=telegram_id, message_text=ai_response, message_type="ai"
            )

            logger.info(f"🤖 AI ответил пользователю {telegram_id}")

            # Логируем успешную активность пользователя
            log_user_activity(telegram_id, "ai_message_sent", True)

            # Записываем активность в родительский контроль (если пользователь - ребенок)
            if user.user_type == "child":
                try:
                    parental_service = ParentalControlService(db)
                    await parental_service.record_child_activity(
                        child_telegram_id=telegram_id,
                        activity_type=ActivityType.AI_INTERACTION,
                        details={
                            "message_length": len(user_message),
                            "response_length": len(ai_response),
                            "history_messages": len(history),
                        },
                        message_content=user_message,
                    )
                except Exception as e:
                    logger.error(f"❌ Ошибка записи активности в родительский контроль: {e}")

        # Отправляем ответ пользователю
        await message.answer(
            text=ai_response,
            parse_mode="Markdown",  # Gemini может использовать markdown форматирование
        )

    except Exception as e:
        logger.error(f"❌ Ошибка обработки сообщения: {e}")

        # Логируем ошибку пользователя
        log_user_activity(telegram_id, "ai_message_error", False, str(e))

        # Отправляем безопасное сообщение об ошибке
        await message.answer(
            text="😔 Ой, что-то пошло не так...\n"
            "Попробуй переформулировать вопрос или напиши /start для перезапуска."
        )


@router.message(F.voice)
async def handle_voice(message: Message):
    """
    Обработка голосовых сообщений
    Использует встроенное распознавание речи Telegram

    Args:
        message: Голосовое сообщение от пользователя
    """
    # Telegram автоматически распознает речь в текст
    if message.text:
        # Если Telegram смог распознать речь, обрабатываем как текст
        logger.info(f"🎤 Голосовое сообщение распознано: {message.text[:50]}...")

        # Логируем активность пользователя
        log_user_activity(message.from_user.id, "voice_message_sent", True)

        # Обрабатываем распознанный текст как обычное сообщение
        await handle_ai_message(message, None)
    else:
        # Если распознавание не сработало
        await message.answer(
            text="🎤 Не удалось распознать речь.\n"
            "Попробуйте говорить четче или напишите текстом! 📝"
        )

        # Логируем неудачную попытку
        log_user_activity(
            message.from_user.id, "voice_recognition_failed", False, "No text recognized"
        )


@router.message(F.photo)
@monitor_performance
async def handle_image(message: Message, state: FSMContext):
    """
    Обработка изображений с помощью Gemini Vision API

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

        # Читаем данные изображения
        image_bytes = image_data.read()

        # Получаем пользователя и его данные
        async with get_db() as db:
            user_service = UserService(db)
            user = await user_service.get_user_by_telegram_id(message.from_user.id)

            if not user:
                await processing_msg.edit_text("❌ Сначала зарегистрируйся командой /start")
                return

                # Инициализируем сервисы
                ai_service = GeminiAIService()
                parental_control = ParentalControlService(db)
                history_service = ChatHistoryService(db)

            # Проверяем модерацию изображения
            is_safe, reason = await ai_service.moderate_image_content(image_bytes)

            if not is_safe:
                # Логируем заблокированное изображение
                await parental_control.log_child_activity(
                    child_telegram_id=message.from_user.id,
                    activity_type=ActivityType.MESSAGE_BLOCKED,
                    message_content=f"[ИЗОБРАЖЕНИЕ] {reason}",
                    alert_level="WARNING",
                    moderation_result={"reason": reason, "type": "image_moderation"},
                )

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
                user_grade=user.grade,
            )

            # Сохраняем в историю
            await history_service.add_message(
                user_telegram_id=message.from_user.id,
                message_text=f"[ИЗОБРАЖЕНИЕ] {caption}" if caption else "[ИЗОБРАЖЕНИЕ]",
                message_type="user",
            )

            await history_service.add_message(
                user_telegram_id=message.from_user.id, message_text=ai_response, message_type="ai"
            )

            # Логируем успешную обработку
            await parental_control.log_child_activity(
                child_telegram_id=message.from_user.id,
                activity_type=ActivityType.MESSAGE_SENT,
                message_content=f"[ИЗОБРАЖЕНИЕ] {caption}" if caption else "[ИЗОБРАЖЕНИЕ]",
                alert_level="INFO",
                moderation_result={"status": "safe", "type": "image_analysis"},
            )

            # Отправляем ответ
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


@router.message(F.document)
@monitor_performance
async def handle_document(message: Message, state: FSMContext):
    """
    Обработка документов (PDF, Word и т.д.)

    Args:
        message: Сообщение с документом
        state: FSM состояние
    """
    try:
        # Проверяем тип документа
        document = message.document

        # Поддерживаемые форматы
        supported_formats = {
            "application/pdf": "PDF",
            "application/msword": "Word",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word",
            "text/plain": "Текстовый файл",
        }

        file_type = supported_formats.get(document.mime_type, "Неизвестный формат")

        # Проверяем размер файла (максимум 20MB)
        if document.file_size > 20 * 1024 * 1024:
            await message.answer(
                "📄 Файл слишком большой! Максимум 20MB. "
                "Попробуй сжать документ или скопировать текст 📏"
            )
            return

        # Показываем информацию о файле
        await message.answer(
            f"📄 Получен документ: {document.file_name}\n"
            f"Тип: {file_type}\n"
            f"Размер: {document.file_size / 1024:.1f} KB\n\n"
            "Для полноценной обработки документов нужно больше времени на разработку. "
            "Пока лучше скопируй текст задачи и отправь текстом — я помогу! 📝"
        )

        # Логируем попытку отправки документа
        log_user_activity(
            message.from_user.id,
            "document_upload",
            True,
            f"Type: {file_type}, Size: {document.file_size}",
        )

    except Exception as e:
        logger.error(f"❌ Ошибка обработки документа: {e}")
        await message.answer(
            "📄 Произошла ошибка при обработке документа. " "Попробуй отправить текст задачи! 📝"
        )
        log_user_activity(message.from_user.id, "document_error", False, str(e))
