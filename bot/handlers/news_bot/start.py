"""
Handler команды /start для новостного бота.

Приветствие и показ новостей сразу.
"""

import contextlib

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.database import get_db
from bot.keyboards.news_bot.categories_kb import get_categories_keyboard
from bot.services.news.repository import NewsRepository
from bot.services.news_bot.user_preferences_service import UserPreferencesService
from bot.services.user_service import UserService

router = Router(name="news_bot_start")


def register_handlers(router_instance: Router) -> None:
    """Зарегистрировать handlers в роутере."""
    router_instance.message.register(cmd_start, CommandStart())
    router_instance.message.register(cmd_start, Command("start"))


async def cmd_start(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /start.

    Приветствие и показ новостей сразу.
    """
    try:
        telegram_id = message.from_user.id
        first_name = message.from_user.first_name or "друг"

        logger.info(
            f"📰 /start в новостном боте: user={telegram_id}, "
            f"bot_id={message.bot.id if hasattr(message, 'bot') else 'unknown'}"
        )

        # Регистрируем пользователя если нужно
        with get_db() as db:
            user_service = UserService(db)
            user_service.get_or_create_user(
                telegram_id=telegram_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )

            # Получаем предпочтения
            prefs_service = UserPreferencesService(db)
            prefs = prefs_service.get_or_create_preferences(telegram_id)

            # Получаем новости
            repository = NewsRepository(db)
            categories = prefs.get("categories", [])

            if categories:
                all_news = []
                for category in categories:
                    items = repository.find_by_category(
                        category=category, age=None, grade=None, limit=3
                    )
                    all_news.extend(items)
                raw_list = all_news[:10]
            else:
                raw_list = repository.find_recent(limit=10)

            # Копируем данные в dicts — объекты News нельзя использовать после выхода из сессии
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

        # Приветствие
        welcome_text = (
            f"👋 Привет, {first_name}!\n\n"
            "Я PandaPal News — бот с интересными новостями для детей!\n\n"
        )

        if categories:
            welcome_text += f"📂 Выбраны категории: {', '.join(categories)}\n\n"
        else:
            welcome_text += "📰 Показываю новости из всех категорий\n\n"

        welcome_text += "Используй команды:\n"
        welcome_text += "/news — последние новости\n"
        welcome_text += "/categories — выбор категорий\n"
        welcome_text += "/settings — настройки"

        await message.answer(
            welcome_text, reply_markup=get_categories_keyboard(selected_categories=categories)
        )

        # Показываем новости если есть
        if news_list:
            from bot.keyboards.news_bot.categories_kb import get_category_emoji
            from bot.keyboards.news_bot.news_navigation_kb import get_news_navigation_keyboard

            news = news_list[0]
            category_emoji = get_category_emoji(news["category"])
            max_content_length = 900
            content = news["content"]
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
                f"{category_emoji} <b>{news['title']}</b>\n"
                f"📂 {news['category'].capitalize()}\n\n"
                f"{content}"
            )

            if news.get("image_url"):
                await message.answer_photo(
                    news["image_url"],
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=get_news_navigation_keyboard(
                        news["id"], has_next=len(news_list) > 1, has_prev=False
                    ),
                )
            else:
                await message.answer(
                    text,
                    parse_mode="HTML",
                    reply_markup=get_news_navigation_keyboard(
                        news["id"], has_next=len(news_list) > 1, has_prev=False
                    ),
                )

            with get_db() as db:
                prefs_service = UserPreferencesService(db)
                prefs_service.mark_news_read(telegram_id, news["id"])

            await state.update_data(news_list_ids=[n["id"] for n in news_list], current_index=0)
        else:
            await message.answer(
                "😔 Пока нет новостей.\n\n"
                "Попробуй позже или выбери другие категории через /categories"
            )

        await state.clear()
        logger.info(f"📰 /start обработан успешно для пользователя {telegram_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка обработки /start в новостном боте: {e}", exc_info=True)
        with contextlib.suppress(Exception):
            await message.answer("❌ Произошла ошибка. Попробуй позже или напиши /help")
