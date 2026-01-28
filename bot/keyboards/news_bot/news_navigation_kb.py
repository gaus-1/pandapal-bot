"""
Клавиатура навигации по новостям.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_news_navigation_keyboard(
    news_id: int, has_next: bool = True, has_prev: bool = False
) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру навигации по новостям.

    Args:
        news_id: ID текущей новости
        has_next: Есть ли следующая новость
        has_prev: Есть ли предыдущая новость

    Returns:
        InlineKeyboardMarkup: Клавиатура навигации
    """
    buttons = []

    nav_row = []
    if has_prev:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"news_prev:{news_id}"))
    if has_next:
        nav_row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"news_next:{news_id}"))
    if nav_row:
        buttons.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_news_actions_keyboard(news_id: int) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру действий с новостью.

    Args:
        news_id: ID новости

    Returns:
        InlineKeyboardMarkup: Клавиатура действий
    """
    buttons = [
        [
            InlineKeyboardButton(
                text="🔗 Открыть источник", url="..."
            ),  # URL будет установлен динамически
            InlineKeyboardButton(text="📤 Поделиться", callback_data=f"news_share:{news_id}"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад к новостям", callback_data="news_back"),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)
