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

        # Получаем персонализированные новости
        repository = NewsRepository(db)
        age = prefs.get("age")
        grade = prefs.get("grade")
        categories = prefs.get("categories", [])

        if categories:
            # Если выбраны категории, берем из них
            all_news = []
            for category in categories:
                news = repository.find_by_category(category=category, age=age, grade=grade, limit=3)
                all_news.extend(news)
            news_list = all_news[:5]
        elif age:
            news_list = repository.find_by_age(age, limit=5)
        elif grade:
            news_list = repository.find_by_grade(grade, limit=5)
        else:
            news_list = repository.find_recent(limit=5)

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
        text = f"<b>{news.title}</b>\n\n{news.content[:1000]}"

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
