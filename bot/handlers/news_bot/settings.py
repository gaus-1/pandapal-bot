"""
Handler команды /settings для настроек новостного бота.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.database import get_db
from bot.keyboards.news_bot.settings_kb import get_settings_keyboard
from bot.services.news_bot.user_preferences_service import UserPreferencesService

router = Router(name="news_bot_settings")


def register_handlers(router_instance: Router) -> None:
    """Зарегистрировать handlers в роутере."""
    router_instance.message.register(cmd_settings, Command("settings"))


async def cmd_settings(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /settings.

    Показывает настройки новостного бота.
    """
    telegram_id = message.from_user.id

    logger.info(f"⚙️ /settings: user={telegram_id}")

    with get_db() as db:
        prefs_service = UserPreferencesService(db)
        prefs = prefs_service.get_or_create_preferences(telegram_id)

        categories = prefs.get("categories", [])
        notifications = "включена" if prefs.get("daily_notifications") else "выключена"

        text = (
            f"⚙️ <b>Настройки новостного бота</b>\n\n"
            f"📂 Категории: {', '.join(categories) if categories else 'не выбраны (все категории)'}\n"
            f"🔔 Ежедневная рассылка: {notifications}\n\n"
            "Выбери, что хочешь изменить:"
        )

        await message.answer(text, parse_mode="HTML", reply_markup=get_settings_keyboard())
        await state.clear()
