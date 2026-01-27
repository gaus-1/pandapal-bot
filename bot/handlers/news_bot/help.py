"""
Handler команды /help для новостного бота.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

router = Router(name="news_bot_help")


def register_handlers(router_instance: Router) -> None:
    """Зарегистрировать handlers в роутере."""
    router_instance.message.register(cmd_help, Command("help"))


async def cmd_help(message: Message) -> None:
    """
    Обработчик команды /help.

    Показывает справку по командам новостного бота.
    """
    telegram_id = message.from_user.id

    logger.info(f"❓ /help: user={telegram_id}")

    help_text = (
        "📰 <b>PandaPal News — Справка</b>\n\n"
        "<b>Команды:</b>\n"
        "/start — приветствие и настройка\n"
        "/news — последние новости\n"
        "/categories — выбор категорий\n"
        "/settings — настройки (возраст, класс, категории)\n"
        "/help — эта справка\n\n"
        "<b>Категории новостей:</b>\n"
        "🎮 Игры\n"
        "👗 Мода\n"
        "📚 Образование\n"
        "🍕 Еда\n"
        "⚽ Спорт\n"
        "🐾 Животные\n"
        "🌳 Природа\n"
        "💡 Факты\n"
        "📰 События\n"
        "😄 Приколы\n\n"
        "Все новости адаптированы для детей и проверены модераторами!"
    )

    await message.answer(help_text, parse_mode="HTML")
