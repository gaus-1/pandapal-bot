"""
Handlers для callback queries новостного бота.

Навигация по новостям, выбор категорий, настройки.
"""

import contextlib

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from loguru import logger

from bot.database import get_db
from bot.keyboards.news_bot.categories_kb import get_categories_keyboard
from bot.keyboards.news_bot.settings_kb import get_settings_keyboard
from bot.models.news import News
from bot.services.news_bot.user_preferences_service import UserPreferencesService

router = Router(name="news_bot_callbacks")


def register_handlers(router_instance: Router) -> None:
    """Зарегистрировать handlers в роутере."""
    router_instance.callback_query.register(
        handle_category_toggle, F.data.startswith("news_category:")
    )
    router_instance.callback_query.register(
        handle_categories_done, F.data == "news_categories_done"
    )
    router_instance.callback_query.register(handle_news_next, F.data.startswith("news_next:"))
    router_instance.callback_query.register(handle_news_prev, F.data.startswith("news_prev:"))
    router_instance.callback_query.register(handle_settings, F.data == "news_settings")
    router_instance.callback_query.register(handle_back, F.data == "news_back")


async def handle_category_toggle(callback: CallbackQuery, state: FSMContext) -> None:  # noqa: ARG001
    """Обработка переключения категории."""
    try:
        category = callback.data.split(":")[1]
        telegram_id = callback.from_user.id

        with get_db() as db:
            prefs_service = UserPreferencesService(db)
            prefs = prefs_service.get_or_create_preferences(telegram_id)
            categories = prefs.get("categories", [])

            # Переключаем категорию
            if category in categories:
                categories.remove(category)
            else:
                categories.append(category)

            prefs_service.update_categories(telegram_id, categories)

            # Обновляем клавиатуру
            await callback.message.edit_reply_markup(
                reply_markup=get_categories_keyboard(selected_categories=categories)
            )

    except Exception as e:
        logger.error(f"❌ Ошибка переключения категории: {e}")
        await callback.answer("Ошибка", show_alert=True)


async def handle_categories_done(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка завершения выбора категорий."""
    try:
        telegram_id = callback.from_user.id

        with get_db() as db:
            prefs_service = UserPreferencesService(db)
            prefs = prefs_service.get_or_create_preferences(telegram_id)
            categories = prefs.get("categories", [])

        if categories:
            text = f"✅ Выбрано категорий: {len(categories)}\n\nИспользуй /news для просмотра новостей!"
        else:
            text = "ℹ️ Категории не выбраны. Новости будут показываться из всех категорий."

        await callback.message.edit_text(text)
        await state.clear()

    except Exception as e:
        logger.error(f"❌ Ошибка завершения выбора категорий: {e}")
        await callback.answer("Ошибка", show_alert=True)


async def handle_news_next(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка перехода к следующей новости."""
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

        from bot.keyboards.news_bot.categories_kb import get_category_emoji
        from bot.keyboards.news_bot.news_navigation_kb import get_news_navigation_keyboard

        category_emoji = get_category_emoji(news_data["category"])
        max_content_length = 900
        content = news_data["content"]
        if len(content) > max_content_length:
            cut_point = content.rfind(".", 0, max_content_length)
            if cut_point > max_content_length * 0.7:
                content = content[: cut_point + 1] + "\n\n..."
            else:
                cut_point = content.rfind(" ", 0, max_content_length)
                if cut_point > max_content_length * 0.7:
                    content = content[:cut_point] + "..."
                else:
                    content = content[:max_content_length] + "..."

        text = (
            f"{category_emoji} <b>{news_data['title']}</b>\n"
            f"📂 {news_data['category'].capitalize()}\n\n"
            f"{content}"
        )

        keyboard = get_news_navigation_keyboard(
            news_data["id"],
            has_next=next_index < len(news_ids) - 1,
            has_prev=next_index > 0,
        )

        # Если сообщение с фото — удаляем и отправляем новое
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
        logger.error(f"❌ Ошибка перехода к следующей новости: {e}", exc_info=True)


async def handle_news_prev(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка перехода к предыдущей новости."""
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

        from bot.keyboards.news_bot.categories_kb import get_category_emoji
        from bot.keyboards.news_bot.news_navigation_kb import get_news_navigation_keyboard

        category_emoji = get_category_emoji(news_data["category"])
        max_content_length = 900
        content = news_data["content"]
        if len(content) > max_content_length:
            cut_point = content.rfind(".", 0, max_content_length)
            if cut_point > max_content_length * 0.7:
                content = content[: cut_point + 1] + "\n\n..."
            else:
                cut_point = content.rfind(" ", 0, max_content_length)
                if cut_point > max_content_length * 0.7:
                    content = content[:cut_point] + "..."
                else:
                    content = content[:max_content_length] + "..."

        text = (
            f"{category_emoji} <b>{news_data['title']}</b>\n"
            f"📂 {news_data['category'].capitalize()}\n\n"
            f"{content}"
        )

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
        logger.error(f"❌ Ошибка перехода к предыдущей новости: {e}", exc_info=True)


async def handle_settings(callback: CallbackQuery) -> None:
    """Обработка открытия настроек."""
    await callback.answer()
    try:
        telegram_id = callback.from_user.id

        with get_db() as db:
            prefs_service = UserPreferencesService(db)
            prefs = prefs_service.get_or_create_preferences(telegram_id)

            categories = prefs.get("categories", [])
            notifications = "включена" if prefs.get("daily_notifications") else "выключена"

            text = (
                f"⚙️ <b>Настройки</b>\n\n"
                f"📂 Категории: {', '.join(categories) if categories else 'не выбраны (все категории)'}\n"
                f"🔔 Рассылка: {notifications}"
            )

            if callback.message.photo:
                with contextlib.suppress(Exception):
                    await callback.message.delete()
                await callback.message.answer(
                    text, parse_mode="HTML", reply_markup=get_settings_keyboard()
                )
            else:
                await callback.message.edit_text(
                    text, parse_mode="HTML", reply_markup=get_settings_keyboard()
                )

    except Exception as e:
        logger.error(f"❌ Ошибка открытия настроек: {e}", exc_info=True)


async def handle_back(callback: CallbackQuery) -> None:
    """Обработка кнопки 'Назад'."""
    try:
        await callback.message.edit_text("🔙 Возвращаемся назад...")
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка возврата назад: {e}")
        await callback.answer("Ошибка", show_alert=True)
