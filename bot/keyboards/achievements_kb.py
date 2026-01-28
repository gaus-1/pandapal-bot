"""
Клавиатуры для системы достижений и геймификации PandaPal.

Этот модуль содержит все inline клавиатуры для системы достижений,
позволяющие пользователям просматривать свой прогресс, награды
и участвовать в образовательных челленджах.

Основные клавиатуры:
- get_achievements_keyboard() - Главное меню достижений
- get_achievement_details_keyboard() - Детали конкретного достижения
- get_leaderboard_keyboard() - Рейтинг пользователей
- get_challenges_keyboard() - Активные челленджи

Все клавиатуры используют inline кнопки для интерактивности
и оптимизированы для мобильных устройств.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_achievements_keyboard() -> InlineKeyboardMarkup:
    """
    Создает главную клавиатуру для системы достижений.

    Предоставляет пользователям доступ к основным разделам системы
    достижений: просмотр собственных достижений, доступных наград,
    рейтинга и активных челленджей.

    Returns:
        InlineKeyboardMarkup: Inline клавиатура с кнопками достижений.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏅 Мои достижения", callback_data="achievements:my"),
            ],
            [
                InlineKeyboardButton(
                    text="🎯 Доступные награды", callback_data="achievements:available"
                ),
            ],
            [
                InlineKeyboardButton(text="📈 Рейтинг", callback_data="achievements:leaderboard"),
            ],
            [
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="menu:main"),
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
                InlineKeyboardButton(text="📊 Общая статистика", callback_data="progress:overall"),
            ],
            [
                InlineKeyboardButton(text="📚 По предметам", callback_data="progress:subjects"),
            ],
            [
                InlineKeyboardButton(text="📅 По дням", callback_data="progress:daily"),
            ],
            [
                InlineKeyboardButton(text="🏆 Достижения", callback_data="achievements:my"),
            ],
            [
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="menu:main"),
            ],
        ]
    )

    return keyboard
