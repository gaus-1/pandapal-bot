"""
Обработчик общения с AI
Главная функция бота — диалог с PandaPalAI
@module bot.handlers.ai_chat
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.database import get_db
from bot.services import (
    ChatHistoryService,
    ContentModerationService,
    GeminiAIService,
    UserService,
)
from bot.monitoring import log_user_activity, monitor_performance

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
        # Проверка контента на безопасность
        moderation_service = ContentModerationService()
        is_safe, reason = moderation_service.is_safe_content(user_message)

        if not is_safe:
            logger.warning(f"🚫 Заблокирован контент от {telegram_id}: {reason}")

            # Логируем заблокированный контент
            moderation_service.log_blocked_content(telegram_id, user_message, reason)
            
            # Логируем активность пользователя
            log_user_activity(telegram_id, "blocked_content", False, reason)

            # Отправляем безопасный ответ
            safe_response = moderation_service.get_safe_response_alternative(
                "blocked_content"
            )
            await message.answer(text=safe_response)
            return

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


@router.message(F.photo)
async def handle_photo(message: Message):
    """
    Обработка фотографий (задачи с фото, графики и т.д.)
    TODO: Реализовать распознавание через Gemini Vision

    Args:
        message: Сообщение с фото
    """
    await message.answer(
        text="📷 Обработка изображений скоро появится!\n"
        "Пока опиши задачу текстом — я помогу! 🐼"
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
        log_user_activity(message.from_user.id, "voice_recognition_failed", False, "No text recognized")


@router.message(F.document)
async def handle_document(message: Message):
    """
    Обработка документов (PDF, Word и т.д.)
    TODO: Реализовать парсинг документов

    Args:
        message: Сообщение с документом
    """
    await message.answer(
        text="📄 Обработка файлов скоро появится!\n"
        "Пока скопируй текст задачи сюда — я помогу! 📝"
    )
