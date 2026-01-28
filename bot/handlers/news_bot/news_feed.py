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
BRIEF_CONTENT_LENGTH = 150
DELAY_BETWEEN_MESSAGES = 0.05

CATEGORY_EMOJIS = {
    "спорт": "⚽",
    "образование": "📚",
    "игры": "🎮",
    "мода": "👗",
    "еда": "🍕",
    "животные": "🐾",
    "природа": "🌳",
    "факты": "💡",
    "события": "📰",
    "приколы": "😄",
}


def register_handlers(router_instance: Router) -> None:
    router_instance.message.register(cmd_news, Command("news"))


def _format_item(news: dict) -> str:
    title = news["title"]
    category = news.get("category", "события")
    emoji = CATEGORY_EMOJIS.get(category, "📰")

    content = news.get("content", "") or ""
    if content:
        if len(content) > BRIEF_CONTENT_LENGTH:
            cut = content.rfind(".", 0, BRIEF_CONTENT_LENGTH)
            if cut > BRIEF_CONTENT_LENGTH * 0.7:
                content = content[: cut + 1]
            else:
                cut = content.rfind(" ", 0, BRIEF_CONTENT_LENGTH)
                content = content[: cut if cut > 0 else BRIEF_CONTENT_LENGTH] + "..."
        brief = f"\n\n{content}"
    else:
        brief = ""

    return f"{emoji} <b>{title}</b>{brief}"


async def cmd_news(message: Message) -> None:
    """Новости потоком — каждое сообщением, пользователь скроллит вниз."""
    telegram_id = message.from_user.id
    logger.info(f"📰 /news: user={telegram_id}")

    with get_db() as db:
        prefs_service = UserPreferencesService(db)
        prefs = prefs_service.get_or_create_preferences(telegram_id)
        read_ids = set(prefs.get("read_news_ids", []) or [])

        repository = NewsRepository(db)
        raw_list = repository.find_recent(limit=MAX_NEWS * 2)

        seen_titles = set()
        news_list = []
        for n in raw_list:
            if n.id in read_ids:
                continue
            title_lower = n.title.lower().strip()
            if title_lower in seen_titles:
                continue
            seen_titles.add(title_lower)
            news_list.append(
                {
                    "id": n.id,
                    "title": n.title,
                    "content": n.content or "",
                    "category": n.category or "события",
                    "image_url": getattr(n, "image_url", None),
                }
            )
            if len(news_list) >= MAX_NEWS:
                break

    if not news_list:
        await message.answer("📰 Новости загружаются. Обновляю каждые 30 минут.")
        return

    with get_db() as db:
        prefs_service = UserPreferencesService(db)
        for i, news in enumerate(news_list):
            text = _format_item(news)
            if i > 0:
                text = "━━━━━━━━━━━━━━━━━━━━\n\n" + text

            if news.get("image_url"):
                await message.answer_photo(news["image_url"], caption=text, parse_mode="HTML")
            else:
                await message.answer(text, parse_mode="HTML")
            prefs_service.mark_news_read(telegram_id, news["id"])
            if (i + 1) % 20 == 0:
                await asyncio.sleep(0.5)
            else:
                await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
