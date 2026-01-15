"""
Обработчик команды /start для Telegram бота PandaPal.

Этот модуль реализует стартовую точку взаимодействия с ботом.
Обрабатывает первичную регистрацию пользователей, приветственные сообщения
и инициализацию главного меню.

Основные возможности:
- Автоматическая регистрация новых пользователей в базе данных
- Получение информации об существующих пользователях
- Отображение персонализированного приветствия
- Защита от дублирования команд (антиспам)
- Логирование всех стартовых взаимодействий
"""

from datetime import datetime

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from loguru import logger

from bot.database import get_db
from bot.keyboards.main_kb import get_main_menu_keyboard
from bot.services.user_service import UserService

# Создаём роутер для обработчиков команды /start
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start - первичная точка входа в бота.

    Выполняет комплексную инициализацию взаимодействия с пользователем:
    регистрацию в БД, валидацию и отправку приветственного сообщения.

    Функциональность:
    1. Регистрация нового пользователя или получение существующего из БД
    2. Защита от дублирования команд (антиспам с таймаутом 2 секунды)
    3. Персонализированное приветственное сообщение
    4. Отображение главного меню с основными функциями бота
    5. Обработка deep links для Premium (start=premium_*)

    Args:
        message (Message): Объект сообщения от Telegram с данными пользователя.
        state (FSMContext): Контекст конечного автомата для управления диалогами.

    Returns:
        None: Функция асинхронная, результат отправляется через message.answer().
    """
    # Получаем данные пользователя из Telegram
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Получаем параметр start (deep link)
    start_param = None
    if message.text and len(message.text.split()) > 1:
        start_param = message.text.split()[1]

    logger.info(f"/start от пользователя {telegram_id} ({first_name}), start_param={start_param}")

    # Обработка deep link для Premium
    if start_param and start_param.startswith("premium_"):
        # #region agent log
        logger.debug(f"Premium deep link detected: user={telegram_id}, param={start_param}")
        # #endregion

        # Парсим план из параметра (premium_week, premium_month, premium_year)
        plan_id = start_param.replace("premium_", "")
        if plan_id in ["week", "month", "year"]:
            logger.info(f"💎 Открываем Premium для user={telegram_id}, plan={plan_id}")

            # Регистрируем пользователя если нужно
            with get_db() as db:
                user_service = UserService(db)
                user_service.get_or_create_user(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                )

            # Открываем Mini App с Premium экраном
            from aiogram.types import WebAppInfo

            from bot.config import settings

            await message.answer(
                text=f"💎 Открываю Premium подписку для тебя, {first_name}!",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🚀 Открыть Premium",
                                web_app=WebAppInfo(url=f"{settings.frontend_url}#premium"),
                            )
                        ]
                    ]
                ),
            )
            await state.clear()
            return

    # #region agent log
    logger.debug(f"Regular start command: user={telegram_id}, param={start_param}")
    # #endregion

    # Защита от дублирования - проверяем время последнего сообщения
    # Используем модульный уровень для хранения временных меток
    if not hasattr(cmd_start, "_last_message_times"):
        cmd_start._last_message_times: dict[int, datetime] = {}  # type: ignore[attr-defined]

    current_time = datetime.now()
    last_message_time = cmd_start._last_message_times  # type: ignore[attr-defined]

    if telegram_id in last_message_time:
        time_diff = (current_time - last_message_time[telegram_id]).total_seconds()
        if time_diff < 2:  # Меньше 2 секунд между сообщениями
            logger.warning(
                f"Пользователь {telegram_id} отправляет сообщения слишком часто, пропускаем"
            )
            return

    # Обновляем время последнего сообщения
    last_message_time[telegram_id] = current_time

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

Я — <b>PandaPal</b> 🐼, твой умный помощник в учёбе!

<b>Что я умею:</b>
✅ Отвечаю на вопросы по всем школьным предметам (1-9 класс)
✅ Решаю задачи с фотографий — просто отправь фото задания
✅ Понимаю голосовые сообщения — говори, я услышу!
✅ Объясняю сложные темы простым языком
✅ Помогаю с домашними заданиями по любому предмету
✅ Играю в развивающие игры (крестики-нолики, шашки, 2048)

<b>Как со мной общаться:</b>
• Напиши любой вопрос — я отвечу!
• Отправь фото с задачей — я решу и объясню
• Запиши голосовое сообщение — я пойму и помогу
• Открой Mini App для игр и удобного чата

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


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Обновить клавиатуру с меню"""
    await message.answer("🎮 Меню обновлено!", reply_markup=get_main_menu_keyboard())
