"""
Обработчики главного меню и навигации бота PandaPal.

Этот модуль содержит все обработчики кнопок главного меню бота,
обеспечивающие навигацию между различными разделами и функциями.

Основные разделы меню:
- 📚 Помощь с уроками (выбор предметов и получение объяснений)
- 🎮 Развивающие игры (интеллектуальные игры и викторины)
- 🏆 Мои достижения (просмотр прогресса и наград)
- ⚙️ Настройки (персонализация профиля)
- 📊 Статистика (аналитика использования)
- ℹ️ О боте (информация и помощь)

Каждый обработчик логирует действия пользователей для аналитики
и обеспечивает корректную навигацию по интерфейсу бота.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from loguru import logger

from bot.database import get_db
from bot.keyboards.main_kb import (
    get_help_type_keyboard,
    get_main_menu_keyboard,
    get_subjects_keyboard,
)
from bot.services.simple_monitor import get_simple_monitor
from bot.services.user_service import UserService

router = Router(name="menu")


@router.message(F.text == "📚 Помощь с уроками")
async def homework_help(message: Message, state: FSMContext):  # noqa: ARG001
    """
    Обработчик кнопки "📚 Помощь с уроками".

    Отображает интерфейс выбора школьных предметов для получения
    помощи с домашними заданиями от AI ассистента.

    Args:
        message (Message): Сообщение пользователя с текстом кнопки.
        state (FSMContext): Контекст FSM для управления состоянием диалога.
    """
    telegram_id = message.from_user.id

    logger.info(f"📚 Пользователь {telegram_id} открыл помощь с уроками")

    await message.answer(
        text="📚 <b>Помощь с уроками</b>\n\nВыбери предмет, с которым нужна помощь:",
        reply_markup=get_subjects_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("subject:"))
async def subject_selected(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора школьного предмета.

    Сохраняет выбранный предмет в FSM состояние и показывает
    варианты помощи (объяснение темы, решение задачи, тест).

    Args:
        callback (CallbackQuery): Callback от нажатия на кнопку предмета.
        state (FSMContext): Контекст FSM для сохранения выбора.
    """
    subject = callback.data.split(":")[1]

    subject_names = {
        "math": "🔢 Математика",
        "russian": "📖 Русский язык",
        "world": "🌍 Окружающий мир",
        "english": "🇬🇧 Английский язык",
        "chemistry": "⚗️ Химия",
        "physics": "🔬 Физика",
        "history": "📜 История",
        "geography": "🌎 География",
        "other": "🎨 Другой предмет",
    }

    subject_name = subject_names.get(subject, subject)

    # Сохраняем выбранный предмет в состояние
    await state.update_data(subject=subject, subject_name=subject_name)

    logger.info(f"Выбран предмет: {subject_name}")

    await callback.message.edit_text(
        text=f"📚 <b>{subject_name}</b>\n\nКак я могу помочь?",
        reply_markup=get_help_type_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


@router.callback_query(F.data.startswith("help:"))
async def help_type_selected(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора типа помощи с предметом.

    Обрабатывает выбор: объяснение темы, решение задачи или прохождение теста.
    Переводит пользователя в режим общения с AI для выбранного типа помощи.

    Args:
        callback (CallbackQuery): Callback от нажатия на кнопку типа помощи.
        state (FSMContext): Контекст FSM с сохраненным предметом.
    """
    help_type = callback.data.split(":")[1]

    # Получаем данные из состояния
    data = await state.get_data()
    subject_name = data.get("subject_name", "предмет")

    help_texts = {
        "solve": f"📝 <b>Решение задачи по {subject_name}</b>\n\n"
        "Отправь мне условие задачи, и я помогу её решить с подробным объяснением!",
        "explain": f"📚 <b>Объяснение темы по {subject_name}</b>\n\n"
        "Напиши, какую тему нужно объяснить, и я расскажу простыми словами!",
        "check": f"✅ <b>Проверка ответа по {subject_name}</b>\n\n"
        "Отправь задачу и свой ответ, я проверю правильность и объясню ошибки!",
        "hint": f"💡 <b>Подсказка по {subject_name}</b>\n\n"
        "Опиши задачу, и я дам тебе подсказку, чтобы ты смог решить её сам!",
    }

    response_text = help_texts.get(help_type, "Напиши свой вопрос!")

    # Сохраняем режим помощи
    await state.update_data(help_mode=help_type)

    await callback.message.edit_text(text=response_text, parse_mode="HTML")

    await callback.answer()


@router.message(F.text == "📊 Мой прогресс")
async def show_progress(message: Message, state: FSMContext):  # noqa: ARG001
    """
    Обработчик кнопки "📊 Мой прогресс"
    Показывает статистику и достижения
    """
    telegram_id = message.from_user.id

    logger.info(f"📊 Пользователь {telegram_id} открыл прогресс")

    with get_db() as db:
        user_service = UserService(db)

        user = user_service.get_user_by_telegram_id(telegram_id)

        if not user:
            await message.answer("❌ Пользователь не найден. Напиши /start для регистрации.")
            return

        # Получаем статистику через упрощенный монитор
        try:
            get_simple_monitor()
            # Пока заглушка - статистика будет позже
            analytics = {"total_messages": 0, "total_learning_sessions": 0, "total_time_spent": 0}

            # Формируем текст с прогрессом
            progress_text = f"""
📊 <b>Твой прогресс</b>

👤 <b>Профиль:</b>
• Имя: {user.first_name}
• Класс: {user.grade if user.grade else "Не указан"}
• Возраст: {user.age if user.age else "Не указан"}

📈 <b>Статистика:</b>
• Всего сообщений: {analytics.get("total_messages", 0)}
• Вопросов задано: {analytics.get("questions_asked", 0)}
• Дней с ботом: {analytics.get("days_active", 0)}

🎯 <b>Достижения:</b>
🚧 <i>Система достижений в разработке</i>

💡 <b>Продолжай учиться каждый день!</b>
"""
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            progress_text = f"""
📊 <b>Твой прогресс</b>

👤 <b>Профиль:</b>
• Имя: {user.first_name}
• Класс: {user.grade if user.grade else "Не указан"}
• Возраст: {user.age if user.age else "Не указан"}

💡 <b>Продолжай учиться!</b>
"""

    await message.answer(
        text=progress_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "menu:main")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "🔙 Главное меню"
    Возврат в главное меню
    """
    await state.clear()

    await callback.message.edit_text(
        text="🏠 <b>Главное меню</b>\n\nВыбери действие из меню ниже 👇", parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "premium:info")
async def premium_info_callback(callback: CallbackQuery):
    """
    Обработчик кнопки "💎 Узнать о Premium"
    Показывает информацию о Premium и предлагает открыть Mini App
    """
    from bot.config import settings

    premium_text = """
💎 <b>Premium подписка PandaPal</b>

✨ <b>Что ты получишь:</b>
• Неограниченные вопросы к AI панде
• Помощь по всем школьным предметам
• Игры без ограничений
• Приоритетная поддержка
• Эксклюзивные достижения

🚀 <b>Открой Mini App</b> чтобы узнать больше и оформить подписку!
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Открыть Premium",
                    web_app=WebAppInfo(url=f"{settings.frontend_url}#premium"),
                )
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main"),
            ],
        ]
    )

    await callback.message.edit_text(
        text=premium_text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()
