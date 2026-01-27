"""
Клавиатура выбора категорий новостей.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Категории с эмодзи
CATEGORIES = {
    "игры": "🎮",
    "мода": "👗",
    "образование": "📚",
    "еда": "🍕",
    "спорт": "⚽",
    "животные": "🐾",
    "природа": "🌳",
    "факты": "💡",
    "события": "📰",
    "приколы": "😄",
}


def get_categories_keyboard(selected_categories: list[str] | None = None) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру выбора категорий.

    Args:
        selected_categories: Список выбранных категорий (для отметки)

    Returns:
        InlineKeyboardMarkup: Клавиатура с категориями
    """
    selected = set(selected_categories or [])

    buttons = []
    row = []

    for category, emoji in CATEGORIES.items():
        # Отмечаем выбранные категории
        prefix = "✅ " if category in selected else ""
        text = f"{prefix}{emoji} {category.capitalize()}"

        row.append(
            InlineKeyboardButton(
                text=text,
                callback_data=f"news_category:{category}",
            )
        )

        # По 2 кнопки в ряд
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    # Кнопка "Готово"
    buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="news_categories_done")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_category_emoji(category: str) -> str:
    """Получить эмодзи для категории."""
    return CATEGORIES.get(category, "📰")
