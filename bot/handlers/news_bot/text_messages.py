"""
Обработчик текстовых сообщений: короткий ответ с командами.
"""

from aiogram import F, Router
from aiogram.types import Message

router = Router(name="news_bot_text_messages")


def register_handlers(router_instance: Router) -> None:
    router_instance.message.register(handle_text_message, F.text)


async def handle_text_message(message: Message) -> None:
    """Ответ на произвольный текст: используй /start или /news."""
    await message.answer("Используй /start или /news — там новости.")
