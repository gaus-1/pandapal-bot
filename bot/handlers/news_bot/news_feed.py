"""
Команда /news — те же новости со всех разделов, поток без категорий.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.database import get_db
from bot.keyboards.news_bot.news_navigation_kb import get_news_navigation_keyboard
from bot.services.news.repository import NewsRepository
from bot.services.news_bot.user_preferences_service import UserPreferencesService

router = Router(name="news_bot_feed")

MAX_NEWS = 50
MAX_CONTENT_LENGTH = 900


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


async def cmd_news(message: Message, state: FSMContext) -> None:
    """Новости со всех разделов, без категорий."""
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
                "category": n.category,
                "image_url": getattr(n, "image_url", None),
            }
            for n in raw_list
        ]

    if not news_list:
        await message.answer("📰 Новости загружаются. Обновляю каждые 30 минут.")
        return

    news = news_list[0]
    text = _format_item(news)
    keyboard = get_news_navigation_keyboard(news["id"], has_next=len(news_list) > 1, has_prev=False)

    if news.get("image_url"):
        await message.answer_photo(
            news["image_url"], caption=text, parse_mode="HTML", reply_markup=keyboard
        )
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    with get_db() as db:
        prefs_service = UserPreferencesService(db)
        prefs_service.mark_news_read(telegram_id, news["id"])

    await state.update_data(news_list_ids=[n["id"] for n in news_list], current_index=0)
