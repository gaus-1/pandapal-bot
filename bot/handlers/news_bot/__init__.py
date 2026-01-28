"""
Handlers новостного бота: новости потоком сообщений, пользователь скроллит.
Без кнопок. Обновление каждые 30 минут.
"""

from aiogram import Router

from . import help, news_feed, start, text_messages

router = Router(name="news_bot")

start.register_handlers(router)
news_feed.register_handlers(router)
help.register_handlers(router)
text_messages.register_handlers(router)

__all__ = ["router"]
