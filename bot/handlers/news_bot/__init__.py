"""
Handlers новостного бота: только новости, без категорий и настроек.
Поток новостей 24/7, обновление каждые 30 минут.
"""

from aiogram import Router

from . import callbacks, help, news_feed, start, text_messages

router = Router(name="news_bot")

start.register_handlers(router)
news_feed.register_handlers(router)
help.register_handlers(router)
callbacks.register_handlers(router)
text_messages.register_handlers(router)

__all__ = ["router"]
