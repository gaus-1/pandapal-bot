"""
Handler команды /start для новостного бота.

Сразу показываем новости со всех разделов, без кнопок категорий и настроек.
"""

import contextlib

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.database import get_db
from bot.keyboards.news_bot.news_navigation_kb import get_news_navigation_keyboard
from bot.services.news.repository import NewsRepository
from bot.services.news_bot.user_preferences_service import UserPreferencesService
from bot.services.user_service import UserService

router = Router(name="news_bot_start")

MAX_NEWS_ON_START = 50
MAX_CONTENT_LENGTH = 900


def register_handlers(router_instance: Router) -> None:
    """Зарегистрировать handlers в роутере."""
    router_instance.message.register(cmd_start, CommandStart())
    router_instance.message.register(cmd_start, Command("start"))


def _format_news_item(news: dict) -> str:
    """Форматировать одну новость в текст."""
    title = news["title"]
    content = news["content"] or ""
    if len(content) > MAX_CONTENT_LENGTH:
        cut = content.rfind(".", 0, MAX_CONTENT_LENGTH)
        if cut > MAX_CONTENT_LENGTH * 0.7:
            content = content[: cut + 1] + "\n\n..."
        else:
            cut = content.rfind(" ", 0, MAX_CONTENT_LENGTH)
            content = content[: cut if cut > 0 else MAX_CONTENT_LENGTH] + "..."
    return f"<b>{title}</b>\n\n{content}"


async def cmd_start(message: Message, state: FSMContext) -> None:
    """
    При заходе в бота сразу показываем новости. Без кнопок категорий и Готово.
    """
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
            repository = NewsRepository(db)
            raw_list = repository.find_recent(limit=MAX_NEWS_ON_START)
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
            await message.answer(
                "📰 Новости загружаются. Обновляю каждые 30 минут. Зайди через минуту."
            )
            await state.clear()
            return

        news = news_list[0]
        text = _format_news_item(news)
        keyboard = get_news_navigation_keyboard(
            news["id"], has_next=len(news_list) > 1, has_prev=False
        )

        if news.get("image_url"):
            await message.answer_photo(
                news["image_url"],
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        else:
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

        with get_db() as db:
            prefs_service = UserPreferencesService(db)
            prefs_service.mark_news_read(telegram_id, news["id"])

        await state.update_data(news_list_ids=[n["id"] for n in news_list], current_index=0)
        logger.info(f"📰 /start ok: user={telegram_id}, news_count={len(news_list)}")

    except Exception as e:
        logger.error(f"❌ /start news bot: {e}", exc_info=True)
        with contextlib.suppress(Exception):
            await message.answer("❌ Ошибка. Попробуй /start ещё раз.")
