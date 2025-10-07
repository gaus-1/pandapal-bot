"""
Обработчики главного меню и навигации
Обработка всех кнопок главного меню
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from bot.database import get_db
from bot.keyboards.main_kb import (
    get_main_menu_keyboard,
    get_subjects_keyboard,
    get_help_type_keyboard,
)
from bot.services.user_service import UserService
from bot.services.analytics_service import AnalyticsService

router = Router(name="menu")


@router.message(F.text == "📚 Помощь с уроками")
async def homework_help(message: Message, state: FSMContext):
    """
    Обработчик кнопки "📚 Помощь с уроками"
    Показывает выбор предметов
    """
    telegram_id = message.from_user.id
    
    logger.info(f"📚 Пользователь {telegram_id} открыл помощь с уроками")
    
    await message.answer(
        text="📚 <b>Помощь с уроками</b>\n\n"
        "Выбери предмет, с которым нужна помощь:",
        reply_markup=get_subjects_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("subject:"))
async def subject_selected(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора предмета
    Показывает типы помощи
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
        "other": "🎨 Другой предмет"
    }
    
    subject_name = subject_names.get(subject, subject)
    
    # Сохраняем выбранный предмет в состояние
    await state.update_data(subject=subject, subject_name=subject_name)
    
    logger.info(f"Выбран предмет: {subject_name}")
    
    await callback.message.edit_text(
        text=f"📚 <b>{subject_name}</b>\n\n"
        "Как я могу помочь?",
        reply_markup=get_help_type_keyboard(),
        parse_mode="HTML"
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("help:"))
async def help_type_selected(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора типа помощи
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
                "Опиши задачу, и я дам тебе подсказку, чтобы ты смог решить её сам!"
    }
    
    response_text = help_texts.get(help_type, "Напиши свой вопрос!")
    
    # Сохраняем режим помощи
    await state.update_data(help_mode=help_type)
    
    await callback.message.edit_text(
        text=response_text,
        parse_mode="HTML"
    )
    
    await callback.answer()


@router.message(F.text == "📊 Мой прогресс")
async def show_progress(message: Message, state: FSMContext):
    """
    Обработчик кнопки "📊 Мой прогресс"
    Показывает статистику и достижения
    """
    telegram_id = message.from_user.id
    
    logger.info(f"📊 Пользователь {telegram_id} открыл прогресс")
    
    with get_db() as db:
        analytics_service = AnalyticsService(db)
        user_service = UserService(db)
        
        user = user_service.get_user_by_telegram_id(telegram_id)
        
        if not user:
            await message.answer(
                "❌ Пользователь не найден. Напиши /start для регистрации."
            )
            return
        
        # Получаем статистику
        try:
            analytics = analytics_service.get_user_analytics(telegram_id)
            
            # Формируем текст с прогрессом
            progress_text = f"""
📊 <b>Твой прогресс</b>

👤 <b>Профиль:</b>
• Имя: {user.first_name}
• Класс: {user.grade if user.grade else 'Не указан'}
• Возраст: {user.age if user.age else 'Не указан'}

📈 <b>Статистика:</b>
• Всего сообщений: {analytics.get('total_messages', 0)}
• Вопросов задано: {analytics.get('questions_asked', 0)}
• Дней с ботом: {analytics.get('days_active', 0)}

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
• Класс: {user.grade if user.grade else 'Не указан'}
• Возраст: {user.age if user.age else 'Не указан'}

💡 <b>Продолжай учиться!</b>
"""
    
    await message.answer(
        text=progress_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "menu:main")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "🔙 Главное меню"
    Возврат в главное меню
    """
    await state.clear()
    
    await callback.message.edit_text(
        text="🏠 <b>Главное меню</b>\n\n"
        "Выбери действие из меню ниже 👇",
        parse_mode="HTML"
    )
    
    await callback.answer()

