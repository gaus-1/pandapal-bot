"""
Handlers для callback queries новостного бота.

Навигация по новостям, выбор категорий, настройки.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from loguru import logger

from bot.database import get_db
from bot.keyboards.news_bot.categories_kb import get_categories_keyboard
from bot.keyboards.news_bot.news_navigation_kb import get_news_navigation_keyboard
from bot.keyboards.news_bot.settings_kb import (
    get_age_keyboard,
    get_grade_keyboard,
    get_settings_keyboard,
)
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
    router_instance.callback_query.register(handle_set_age, F.data == "news_set_age")
    router_instance.callback_query.register(handle_set_grade, F.data == "news_set_grade")
    router_instance.callback_query.register(handle_age_select, F.data.startswith("news_age:"))
    router_instance.callback_query.register(handle_grade_select, F.data.startswith("news_grade:"))
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
    try:
        telegram_id = callback.from_user.id

        data = await state.get_data()
        news_ids = data.get("news_list_ids", [])
        current_index = data.get("current_index", 0)

        if current_index < len(news_ids) - 1:
            next_index = current_index + 1
            next_id = news_ids[next_index]

            with get_db() as db:
                news = db.get(News, next_id)

                if news:
                    text = f"<b>{news.title}</b>\n\n{news.content[:1000]}"

                    await callback.message.edit_text(
                        text,
                        parse_mode="HTML",
                        reply_markup=get_news_navigation_keyboard(
                            news.id,
                            has_next=next_index < len(news_ids) - 1,
                            has_prev=next_index > 0,
                        ),
                    )

                    await state.update_data(current_index=next_index)

                    # Отмечаем как прочитанную
                    prefs_service = UserPreferencesService(db)
                    prefs_service.mark_news_read(telegram_id, news.id)

        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка перехода к следующей новости: {e}")
        await callback.answer("Ошибка", show_alert=True)


async def handle_news_prev(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка перехода к предыдущей новости."""
    try:
        data = await state.get_data()
        news_ids = data.get("news_list_ids", [])
        current_index = data.get("current_index", 0)

        if current_index > 0:
            prev_index = current_index - 1
            prev_id = news_ids[prev_index]

            with get_db() as db:
                news = db.get(News, prev_id)

                if news:
                    text = f"<b>{news.title}</b>\n\n{news.content[:1000]}"

                    await callback.message.edit_text(
                        text,
                        parse_mode="HTML",
                        reply_markup=get_news_navigation_keyboard(
                            news.id,
                            has_next=prev_index < len(news_ids) - 1,
                            has_prev=prev_index > 0,
                        ),
                    )

                    await state.update_data(current_index=prev_index)

        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка перехода к предыдущей новости: {e}")
        await callback.answer("Ошибка", show_alert=True)


async def handle_settings(callback: CallbackQuery) -> None:
    """Обработка открытия настроек."""
    try:
        telegram_id = callback.from_user.id

        with get_db() as db:
            prefs_service = UserPreferencesService(db)
            prefs = prefs_service.get_or_create_preferences(telegram_id)

            age = prefs.get("age", "не указан")
            grade = prefs.get("grade", "не указан")
            categories = prefs.get("categories", [])
            notifications = "включена" if prefs.get("daily_notifications") else "выключена"

            text = (
                f"⚙️ <b>Настройки</b>\n\n"
                f"👤 Возраст: {age}\n"
                f"📚 Класс: {grade}\n"
                f"📂 Категории: {', '.join(categories) if categories else 'не выбраны'}\n"
                f"🔔 Рассылка: {notifications}"
            )

            await callback.message.edit_text(
                text, parse_mode="HTML", reply_markup=get_settings_keyboard()
            )

    except Exception as e:
        logger.error(f"❌ Ошибка открытия настроек: {e}")
        await callback.answer("Ошибка", show_alert=True)


async def handle_set_age(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора возраста."""
    try:
        telegram_id = callback.from_user.id

        with get_db() as db:
            prefs_service = UserPreferencesService(db)
            prefs = prefs_service.get_or_create_preferences(telegram_id)
            current_age = prefs.get("age")

        await callback.message.edit_text(
            "👤 Выбери свой возраст:", reply_markup=get_age_keyboard(current_age=current_age)
        )
        await state.set_state("news_setting_age")

    except Exception as e:
        logger.error(f"❌ Ошибка выбора возраста: {e}")
        await callback.answer("Ошибка", show_alert=True)


async def handle_set_grade(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора класса."""
    try:
        telegram_id = callback.from_user.id

        with get_db() as db:
            prefs_service = UserPreferencesService(db)
            prefs = prefs_service.get_or_create_preferences(telegram_id)
            current_grade = prefs.get("grade")

        await callback.message.edit_text(
            "📚 Выбери свой класс:", reply_markup=get_grade_keyboard(current_grade=current_grade)
        )
        await state.set_state("news_setting_grade")

    except Exception as e:
        logger.error(f"❌ Ошибка выбора класса: {e}")
        await callback.answer("Ошибка", show_alert=True)


async def handle_age_select(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора конкретного возраста."""
    try:
        age = int(callback.data.split(":")[1])
        telegram_id = callback.from_user.id

        with get_db() as db:
            prefs_service = UserPreferencesService(db)
            prefs_service.update_age(telegram_id, age)

        await callback.message.edit_text(f"✅ Возраст установлен: {age} лет")
        await state.clear()

        # Предлагаем выбрать класс, если не выбран
        with get_db() as db:
            prefs_service = UserPreferencesService(db)
            prefs = prefs_service.get_or_create_preferences(telegram_id)
            if not prefs.get("grade"):
                await callback.message.answer(
                    "📚 Теперь выбери свой класс:", reply_markup=get_grade_keyboard()
                )
                await state.set_state("news_setting_grade")

    except Exception as e:
        logger.error(f"❌ Ошибка выбора возраста: {e}")
        await callback.answer("Ошибка", show_alert=True)


async def handle_grade_select(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора конкретного класса."""
    try:
        grade = int(callback.data.split(":")[1])
        telegram_id = callback.from_user.id

        with get_db() as db:
            prefs_service = UserPreferencesService(db)
            prefs_service.update_grade(telegram_id, grade)

        await callback.message.edit_text(f"✅ Класс установлен: {grade}")
        await state.clear()

    except Exception as e:
        logger.error(f"❌ Ошибка выбора класса: {e}")
        await callback.answer("Ошибка", show_alert=True)


async def handle_back(callback: CallbackQuery) -> None:
    """Обработка кнопки 'Назад'."""
    try:
        await callback.message.edit_text("🔙 Возвращаемся назад...")
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка возврата назад: {e}")
        await callback.answer("Ошибка", show_alert=True)
