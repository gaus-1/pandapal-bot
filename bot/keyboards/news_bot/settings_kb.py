"""
Клавиатура настроек новостного бота.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_age_keyboard(current_age: int | None = None) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру выбора возраста.

    Args:
        current_age: Текущий возраст (для отметки)

    Returns:
        InlineKeyboardMarkup: Клавиатура выбора возраста
    """
    buttons = []
    row = []

    for age in range(6, 16):
        prefix = "✅ " if age == current_age else ""
        text = f"{prefix}{age} лет"

        row.append(InlineKeyboardButton(text=text, callback_data=f"news_age:{age}"))

        if len(row) == 3:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="news_settings")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_grade_keyboard(current_grade: int | None = None) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру выбора класса.

    Args:
        current_grade: Текущий класс (для отметки)

    Returns:
        InlineKeyboardMarkup: Клавиатура выбора класса
    """
    buttons = []
    row = []

    for grade in range(1, 10):
        prefix = "✅ " if grade == current_grade else ""
        text = f"{prefix}{grade} класс"

        row.append(InlineKeyboardButton(text=text, callback_data=f"news_grade:{grade}"))

        if len(row) == 3:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="news_settings")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """
    Получить главную клавиатуру настроек.

    Returns:
        InlineKeyboardMarkup: Клавиатура настроек
    """
    buttons = [
        [
            InlineKeyboardButton(text="📂 Категории", callback_data="news_set_categories"),
            InlineKeyboardButton(text="🔔 Рассылка", callback_data="news_set_notifications"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="news_back"),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)
