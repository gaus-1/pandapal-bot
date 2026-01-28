"""
Callbacks новостного бота: развернуть/свернуть новость (Читать полностью / Свернуть).
"""

import contextlib

from aiogram import F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from bot.database import get_db
from bot.keyboards.news_bot.news_navigation_kb import get_news_expand_keyboard
from bot.models.news import News

router = Router(name="news_bot_callbacks")

BRIEF_CONTENT_LENGTH = 150
MAX_FULL_LENGTH = 4000

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
    router_instance.callback_query.register(handle_news_full, F.data.startswith("news_full:"))
    router_instance.callback_query.register(handle_news_brief, F.data.startswith("news_brief:"))


def _format_brief(news_data: dict) -> str:
    """Краткий формат: заголовок + до 150 символов."""
    title = news_data["title"]
    category = news_data.get("category", "события")
    emoji = CATEGORY_EMOJIS.get(category, "📰")
    content = news_data.get("content", "") or ""
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


def _format_full(news_data: dict) -> str:
    """Полный формат: заголовок + весь текст (до лимита Telegram)."""
    title = news_data["title"]
    category = news_data.get("category", "события")
    emoji = CATEGORY_EMOJIS.get(category, "📰")
    content = news_data.get("content", "") or ""
    if len(content) > MAX_FULL_LENGTH:
        cut = content.rfind(".", 0, MAX_FULL_LENGTH)
        if cut > MAX_FULL_LENGTH * 0.9:
            content = content[: cut + 1]
        else:
            content = content[:MAX_FULL_LENGTH] + "..."
    return f"{emoji} <b>{title}</b>\n\n{content}" if content else f"{emoji} <b>{title}</b>"


def _news_to_dict(news: News) -> dict:
    return {
        "id": news.id,
        "title": news.title,
        "content": news.content or "",
        "category": news.category or "события",
        "image_url": getattr(news, "image_url", None),
    }


async def handle_news_full(callback: CallbackQuery) -> None:
    """Развернуть новость — показать полный текст."""
    await callback.answer()
    try:
        news_id = int(callback.data.split(":", 1)[1])
        with get_db() as db:
            news = db.get(News, news_id)
            if not news:
                return
            news_data = _news_to_dict(news)

        text = _format_full(news_data)
        keyboard = get_news_expand_keyboard(news_id, expanded=True)

        if callback.message.photo:
            await callback.message.edit_caption(
                caption=text, parse_mode="HTML", reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"❌ news_full: {e}", exc_info=True)
        with contextlib.suppress(Exception):
            await callback.answer("Ошибка", show_alert=True)


async def handle_news_brief(callback: CallbackQuery) -> None:
    """Свернуть новость — показать краткий текст."""
    await callback.answer()
    try:
        news_id = int(callback.data.split(":", 1)[1])
        with get_db() as db:
            news = db.get(News, news_id)
            if not news:
                return
            news_data = _news_to_dict(news)

        text = _format_brief(news_data)
        keyboard = get_news_expand_keyboard(news_id, expanded=False)

        if callback.message.photo:
            await callback.message.edit_caption(
                caption=text, parse_mode="HTML", reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"❌ news_brief: {e}", exc_info=True)
        with contextlib.suppress(Exception):
            await callback.answer("Ошибка", show_alert=True)
