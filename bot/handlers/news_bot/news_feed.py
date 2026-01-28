"""
Команда /news — новости потоком сообщений, пользователь скроллит вниз. Без кнопок.
"""

import asyncio

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from bot.database import get_db
from bot.services.news.repository import NewsRepository
from bot.services.news_bot.user_preferences_service import UserPreferencesService

router = Router(name="news_bot_feed")

MAX_NEWS = 50
MAX_CONTENT_LENGTH = 900
DELAY_BETWEEN_MESSAGES = 0.05


def register_handlers(router_instance: Router) -> None:
    router_instance.message.register(cmd_news, Command("news"))


def _format_item(news: dict) -> str:
    content = news.get("content") or ""
    if len(content) > MAX_CONTENT_LENGTH:
        cut = content.rfind(".", 0, MAX_CONTENT_LENGTH)
        content = (
            content[: (cut + 1 if cut > MAX_CONTENT_LENGTH * 0.7 else MAX_CONTENT_LENGTH)] + "..."
        )
    return f"<b>{news['title']}</b>\n\n{content}"


async def cmd_news(message: Message) -> None:
    """Новости потоком — каждое сообщением, пользователь скроллит вниз."""
    telegram_id = message.from_user.id
    logger.info(f"📰 /news: user={telegram_id}")

    with get_db() as db:
        repository = NewsRepository(db)
        raw_list = repository.find_recent(limit=MAX_NEWS)
        news_list = [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content or "",
                "image_url": getattr(n, "image_url", None),
            }
            for n in raw_list
        ]

    if not news_list:
        await message.answer("📰 Новости загружаются. Обновляю каждые 30 минут.")
        return

    with get_db() as db:
        prefs_service = UserPreferencesService(db)
        for i, news in enumerate(news_list):
            text = _format_item(news)
            if news.get("image_url"):
                await message.answer_photo(news["image_url"], caption=text, parse_mode="HTML")
            else:
                await message.answer(text, parse_mode="HTML")
            prefs_service.mark_news_read(telegram_id, news["id"])
            if (i + 1) % 20 == 0:
                await asyncio.sleep(0.5)
            else:
                await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
