"""
Handler команды /start для новостного бота.

Новости потоком сообщений — пользователь скроллит вниз. Без кнопок.
"""

import asyncio
import contextlib

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from loguru import logger

from bot.database import get_db
from bot.keyboards.news_bot.news_navigation_kb import get_news_expand_keyboard
from bot.services.news.repository import NewsRepository
from bot.services.news_bot.user_preferences_service import UserPreferencesService
from bot.services.user_service import UserService

router = Router(name="news_bot_start")

MAX_NEWS_ON_START = 50
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
    router_instance.message.register(cmd_start, CommandStart())
    router_instance.message.register(cmd_start, Command("start"))


def _format_news_item(news: dict) -> str:
    """Форматировать новость: заголовок + краткое описание."""
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


async def cmd_start(message: Message) -> None:
    """Новости потоком — каждое сообщением, пользователь скроллит вниз."""
    try:
        telegram_id = message.from_user.id
        logger.info(f"📰 /start news bot: user={telegram_id}")

        with get_db() as db:
            user_service = UserService(db)
            user_service.get_or_create_user(
                telegram_id=telegram_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )
            prefs_service = UserPreferencesService(db)
            prefs = prefs_service.get_or_create_preferences(telegram_id)
            read_ids = set(prefs.get("read_news_ids", []) or [])

            repository = NewsRepository(db)
            raw_list = repository.find_recent(limit=MAX_NEWS_ON_START * 2)

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
                if len(news_list) >= MAX_NEWS_ON_START:
                    break

        if not news_list:
            await message.answer(
                "📰 Новости загружаются. Обновляю каждые 30 минут. Зайди через минуту."
            )
            return

        with get_db() as db:
            prefs_service = UserPreferencesService(db)
            for i, news in enumerate(news_list):
                text = _format_news_item(news)
                if i > 0:
                    text = "━━━━━━━━━━━━━━━━━━━━\n\n" + text

                keyboard = get_news_expand_keyboard(news["id"], expanded=False)
                if news.get("image_url"):
                    await message.answer_photo(
                        news["image_url"],
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
                else:
                    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
                prefs_service.mark_news_read(telegram_id, news["id"])
                if (i + 1) % 20 == 0:
                    await asyncio.sleep(0.5)
                else:
                    await asyncio.sleep(DELAY_BETWEEN_MESSAGES)

        logger.info(f"📰 /start ok: user={telegram_id}, news_count={len(news_list)}")

    except Exception as e:
        logger.error(f"❌ /start news bot: {e}", exc_info=True)
        with contextlib.suppress(Exception):
            await message.answer("❌ Ошибка. Попробуй /start ещё раз.")
