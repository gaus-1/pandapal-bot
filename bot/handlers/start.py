"""
Обработчик команды /start
Приветствие нового пользователя и регистрация
@module bot.handlers.start
"""

from datetime import datetime
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.database import get_db
from bot.keyboards.main_kb import get_main_menu_keyboard
from bot.services.user_service import UserService

# Создаём роутер для обработчиков команды /start
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start

    Функционал:
    1. Регистрация нового пользователя или получение существующего
    2. Приветственное сообщение
    3. Отображение главного меню

    Args:
        message: Сообщение от пользователя
        state: FSM состояние (для диалогов)
    """
    # Получаем данные пользователя из Telegram
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    logger.info(f"/start от пользователя {telegram_id} ({first_name})")
    
    # Защита от дублирования - проверяем время последнего сообщения
    current_time = datetime.now()
    last_message_time = getattr(cmd_start, '_last_message_times', {})
    
    if telegram_id in last_message_time:
        time_diff = (current_time - last_message_time[telegram_id]).total_seconds()
        if time_diff < 2:  # Меньше 2 секунд между сообщениями
            logger.warning(f"Пользователь {telegram_id} отправляет сообщения слишком часто, пропускаем")
            return
    
    # Обновляем время последнего сообщения
    if not hasattr(cmd_start, '_last_message_times'):
        cmd_start._last_message_times = {}
    cmd_start._last_message_times[telegram_id] = current_time

    # Работа с базой данных
    with get_db() as db:
        user_service = UserService(db)

        # Получаем или создаём пользователя
        user = user_service.get_or_create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

        # Проверяем, новый ли это пользователь
        is_new_user = user.age is None and user.grade is None

    # Формируем приветственное сообщение
    if is_new_user:
        # Для нового пользователя — подробное приветствие
        welcome_text = f"""
Привет, {first_name}! 👋

Я — <b>PandaPalAI</b> 🐼, твой личный помощник в учёбе!

<b>Что я умею:</b>
✅ Отвечаю на вопросы по любым школьным предметам
✅ Помогаю решать задачи с подробным объяснением
✅ Объясняю сложные темы простым языком
✅ Проверяю твои ответы и даю советы
✅ Поддерживаю и мотивирую тебя! 💪

<b>Как со мной общаться:</b>
• Просто напиши любой вопрос — я отвечу!
• Или выбери действие в меню ниже 👇

<i>Давай начнём! Расскажи, в каком ты классе?</i>
"""
    else:
        # Для существующего пользователя — короткое приветствие
        welcome_text = f"""
С возвращением, {first_name}! 🐼

Рад тебя видеть снова! Чем могу помочь сегодня?
"""

    # Отправляем приветствие с главным меню
    await message.answer(
        text=welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML"
    )

    # Очищаем состояние (на случай если были в диалоге)
    await state.clear()
