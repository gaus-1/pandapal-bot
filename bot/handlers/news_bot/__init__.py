"""
Handlers для новостного бота.

Модульная структура handlers для обработки команд и callback queries.
"""

from aiogram import Router

from . import callbacks, categories, help, news_feed, settings, start, text_messages

# Создаем роутер для новостного бота
router = Router(name="news_bot")

# Регистрируем все handlers (команды сначала, текстовые сообщения в конце)
start.register_handlers(router)
news_feed.register_handlers(router)
categories.register_handlers(router)
settings.register_handlers(router)
help.register_handlers(router)
callbacks.register_handlers(router)
# Текстовые сообщения регистрируем последними, чтобы не перехватывать команды
text_messages.register_handlers(router)

__all__ = ["router"]
