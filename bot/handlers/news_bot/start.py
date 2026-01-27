"""
Handler команды /start для новостного бота.

Приветствие, выбор возраста и класса.
"""

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.database import get_db
from bot.keyboards.news_bot.settings_kb import get_age_keyboard
from bot.services.news_bot.user_preferences_service import UserPreferencesService
from bot.services.user_service import UserService

router = Router(name="news_bot_start")


def register_handlers(router_instance: Router) -> None:
    """Зарегистрировать handlers в роутере."""
    router_instance.message.register(cmd_start, CommandStart())
    router_instance.message.register(cmd_start, Command("start"))


async def cmd_start(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /start.

    Приветствие и настройка предпочтений пользователя.
    """
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name or "друг"

    logger.info(f"📰 /start в новостном боте: user={telegram_id}")

    # Регистрируем пользователя если нужно
    with get_db() as db:
        user_service = UserService(db)
        user_service.get_or_create_user(
            telegram_id=telegram_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

        # Получаем предпочтения
        prefs_service = UserPreferencesService(db)
        prefs = prefs_service.get_or_create_preferences(telegram_id)

    # Проверяем, настроены ли предпочтения
    if not prefs.get("age") or not prefs.get("grade"):
        # Нужно настроить возраст и класс
        welcome_text = (
            f"👋 Привет, {first_name}!\n\n"
            "Я PandaPal News — бот с интересными новостями для детей!\n\n"
            "Чтобы показывать тебе самые интересные новости, мне нужно узнать:\n"
            "1️⃣ Твой возраст\n"
            "2️⃣ Твой класс\n\n"
            "Давай начнем с возраста:"
        )

        await message.answer(welcome_text, reply_markup=get_age_keyboard())
        await state.set_state("news_setting_age")
    else:
        # Предпочтения уже настроены
        age = prefs.get("age")
        grade = prefs.get("grade")

        welcome_text = (
            f"👋 Привет, {first_name}!\n\n"
            f"Я PandaPal News — бот с интересными новостями!\n\n"
            f"Твои настройки:\n"
            f"👤 Возраст: {age} лет\n"
            f"📚 Класс: {grade}\n\n"
            "Используй команды:\n"
            "/news — последние новости\n"
            "/categories — выбор категорий\n"
            "/settings — настройки"
        )

        await message.answer(welcome_text)
        await state.clear()
