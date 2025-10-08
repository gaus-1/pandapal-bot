"""
Клавиатуры для системы достижений и геймификации
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_achievements_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для просмотра достижений
    
    Returns:
        InlineKeyboardMarkup: Клавиатура достижений
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏅 Мои достижения",
                    callback_data="achievements:my"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎯 Доступные награды",
                    callback_data="achievements:available"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📈 Рейтинг",
                    callback_data="achievements:leaderboard"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Главное меню",
                    callback_data="menu:main"
                ),
            ],
        ]
    )
    
    return keyboard


def get_progress_details_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура детального прогресса
    
    Returns:
        InlineKeyboardMarkup: Клавиатура прогресса
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Общая статистика",
                    callback_data="progress:overall"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📚 По предметам",
                    callback_data="progress:subjects"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📅 По дням",
                    callback_data="progress:daily"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Достижения",
                    callback_data="achievements:my"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Главное меню",
                    callback_data="menu:main"
                ),
            ],
        ]
    )
    
    return keyboard

