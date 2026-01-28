"""
Handler команды /news для выдачи новостей.

Пагинация, навигация по новостям.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.database import get_db
from bot.keyboards.news_bot.news_navigation_kb import get_news_navigation_keyboard
from bot.models.news import News
from bot.services.news.repository import NewsRepository
from bot.services.news_bot.user_preferences_service import UserPreferencesService

router = Router(name="news_bot_feed")


def register_handlers(router_instance: Router) -> None:
    """Зарегистрировать handlers в роутере."""
    router_instance.message.register(cmd_news, Command("news"))


async def cmd_news(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /news.

    Выдает последние новости с учетом предпочтений пользователя.
    """
    telegram_id = message.from_user.id

    logger.info(f"📰 /news: user={telegram_id}")

    with get_db() as db:
        # Получаем предпочтения
        prefs_service = UserPreferencesService(db)
        prefs = prefs_service.get_or_create_preferences(telegram_id)

        # Получаем новости
        repository = NewsRepository(db)
        categories = prefs.get("categories", [])

        if categories:
            # Если выбраны категории, берем из них
            all_news = []
            for category in categories:
                news = repository.find_by_category(category=category, age=None, grade=None, limit=3)
                all_news.extend(news)
            news_list = all_news[:10]
        else:
            # Показываем все новости по умолчанию
            news_list = repository.find_recent(limit=10)

        if not news_list:
            await message.answer(
                "😔 Пока нет новостей для тебя.\n\n"
                "Попробуй позже или выбери другие категории через /categories"
            )
            return

        # Отправляем первую новость
        news = news_list[0]
        await _send_news_message(message, news, news_list, 0)

        # Сохраняем индекс в state для навигации
        await state.update_data(news_list_ids=[n.id for n in news_list], current_index=0)


async def _send_news_message(
    message: Message, news: News, news_list: list[News], current_index: int
) -> None:
    """
    Отправить новость пользователю.

    Args:
        message: Сообщение для ответа
        news: Объект News
        news_list: Список всех новостей
        current_index: Текущий индекс
    """
    try:
        from bot.keyboards.news_bot.categories_kb import get_category_emoji

        # Красивое форматирование новости
        category_emoji = get_category_emoji(news.category)
        max_content_length = 900  # Оставляем место для заголовка и форматирования

        # Обрезаем контент, сохраняя целые предложения
        content = news.content
        if len(content) > max_content_length:
            # Ищем последнюю точку перед лимитом
            cut_point = content.rfind(".", 0, max_content_length)
            if cut_point > max_content_length * 0.7:  # Если точка не слишком близко к началу
                content = content[: cut_point + 1] + "\n\n..."
            else:
                # Если точки нет, обрезаем по пробелу
                cut_point = content.rfind(" ", 0, max_content_length)
                if cut_point > max_content_length * 0.7:
                    content = content[:cut_point] + "..."
                else:
                    content = content[:max_content_length] + "..."

        text = (
            f"{category_emoji} <b>{news.title}</b>\n"
            f"📂 {news.category.capitalize()}\n\n"
            f"{content}"
        )

        if news.image_url:
            await message.answer_photo(
                news.image_url,
                caption=text,
                parse_mode="HTML",
                reply_markup=get_news_navigation_keyboard(
                    news.id, has_next=current_index < len(news_list) - 1, has_prev=current_index > 0
                ),
            )
        else:
            await message.answer(
                text,
                parse_mode="HTML",
                reply_markup=get_news_navigation_keyboard(
                    news.id, has_next=current_index < len(news_list) - 1, has_prev=current_index > 0
                ),
            )

        # Отмечаем как прочитанную
        with get_db() as db:
            prefs_service = UserPreferencesService(db)
            prefs_service.mark_news_read(message.from_user.id, news.id)

    except Exception as e:
        logger.error(f"❌ Ошибка отправки новости: {e}")
