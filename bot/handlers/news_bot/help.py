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
        "📰 <b>PandaPal News</b>\n\n"
        "<b>Команды:</b>\n"
        "/start — сразу показываются новости\n"
        "/news — последние новости\n"
        "/help — эта справка\n\n"
        "Новости со всех разделов всех ресурсов. Обновление каждые 30 минут. Поток 24/7."
    )

    await message.answer(help_text, parse_mode="HTML")
