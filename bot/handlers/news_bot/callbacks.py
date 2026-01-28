"""
Callbacks новостного бота: только навигация по новостям (дальше / назад).
Без категорий, настроек и кнопки Готово.
"""

import contextlib

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from loguru import logger

from bot.database import get_db
from bot.keyboards.news_bot.news_navigation_kb import get_news_navigation_keyboard
from bot.models.news import News
from bot.services.news_bot.user_preferences_service import UserPreferencesService

router = Router(name="news_bot_callbacks")

MAX_CONTENT_LENGTH = 900


def register_handlers(router_instance: Router) -> None:
    """Только next/prev по новостям."""
    router_instance.callback_query.register(handle_news_next, F.data.startswith("news_next:"))
    router_instance.callback_query.register(handle_news_prev, F.data.startswith("news_prev:"))


def _format_text(news_data: dict) -> str:
    """Форматировать текст новости."""
    content = news_data.get("content") or ""
    if len(content) > MAX_CONTENT_LENGTH:
        cut = content.rfind(".", 0, MAX_CONTENT_LENGTH)
        if cut > MAX_CONTENT_LENGTH * 0.7:
            content = content[: cut + 1] + "\n\n..."
        else:
            cut = content.rfind(" ", 0, MAX_CONTENT_LENGTH)
            content = content[: cut if cut > 0 else MAX_CONTENT_LENGTH] + "..."
    return f"<b>{news_data['title']}</b>\n\n{content}"


async def handle_news_next(callback: CallbackQuery, state: FSMContext) -> None:
    """Следующая новость."""
    await callback.answer()
    try:
        telegram_id = callback.from_user.id
        data = await state.get_data()
        news_ids = data.get("news_list_ids", [])
        current_index = data.get("current_index", 0)
        if current_index >= len(news_ids) - 1:
            return
        next_index = current_index + 1
        next_id = news_ids[next_index]

        with get_db() as db:
            news = db.get(News, next_id)
            if not news:
                return
            news_data = {
                "id": news.id,
                "title": news.title,
                "content": news.content or "",
                "category": news.category,
                "image_url": getattr(news, "image_url", None),
            }
            prefs_service = UserPreferencesService(db)
            prefs_service.mark_news_read(telegram_id, news.id)

        text = _format_text(news_data)
        keyboard = get_news_navigation_keyboard(
            news_data["id"],
            has_next=next_index < len(news_ids) - 1,
            has_prev=next_index > 0,
        )

        if callback.message.photo:
            with contextlib.suppress(Exception):
                await callback.message.delete()
            if news_data.get("image_url"):
                await callback.message.answer_photo(
                    news_data["image_url"], caption=text, parse_mode="HTML", reply_markup=keyboard
                )
            else:
                await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        else:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)

        await state.update_data(current_index=next_index)
    except Exception as e:
        logger.error(f"❌ news next: {e}", exc_info=True)


async def handle_news_prev(callback: CallbackQuery, state: FSMContext) -> None:
    """Предыдущая новость."""
    await callback.answer()
    try:
        data = await state.get_data()
        news_ids = data.get("news_list_ids", [])
        current_index = data.get("current_index", 0)
        if current_index <= 0:
            return
        prev_index = current_index - 1
        prev_id = news_ids[prev_index]

        with get_db() as db:
            news = db.get(News, prev_id)
            if not news:
                return
            news_data = {
                "id": news.id,
                "title": news.title,
                "content": news.content or "",
                "category": news.category,
                "image_url": getattr(news, "image_url", None),
            }

        text = _format_text(news_data)
        keyboard = get_news_navigation_keyboard(
            news_data["id"],
            has_next=prev_index < len(news_ids) - 1,
            has_prev=prev_index > 0,
        )

        if callback.message.photo:
            with contextlib.suppress(Exception):
                await callback.message.delete()
            if news_data.get("image_url"):
                await callback.message.answer_photo(
                    news_data["image_url"], caption=text, parse_mode="HTML", reply_markup=keyboard
                )
            else:
                await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        else:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)

        await state.update_data(current_index=prev_index)
    except Exception as e:
        logger.error(f"❌ news prev: {e}", exc_info=True)
