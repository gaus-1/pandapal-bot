"""
Handler команды /categories для выбора категорий новостей.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.database import get_db
from bot.keyboards.news_bot.categories_kb import get_categories_keyboard
from bot.services.news_bot.user_preferences_service import UserPreferencesService

router = Router(name="news_bot_categories")


def register_handlers(router_instance: Router) -> None:
    """Зарегистрировать handlers в роутере."""
    router_instance.message.register(cmd_categories, Command("categories"))


async def cmd_categories(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /categories.

    Показывает клавиатуру выбора категорий.
    """
    telegram_id = message.from_user.id

    logger.info(f"📂 /categories: user={telegram_id}")

    with get_db() as db:
        prefs_service = UserPreferencesService(db)
        prefs = prefs_service.get_or_create_preferences(telegram_id)

        selected = prefs.get("categories", [])

        text = (
            "📂 Выбери категории новостей, которые тебе интересны:\n\n"
            "Можно выбрать несколько категорий. "
            "Новости будут подбираться специально для тебя!"
        )

        await message.answer(
            text, reply_markup=get_categories_keyboard(selected_categories=selected)
        )
        await state.set_state("news_selecting_categories")
