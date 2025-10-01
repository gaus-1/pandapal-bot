"""
Основные клавиатуры для Telegram бота
Reply и Inline кнопки для навигации
@module bot.keyboards.main_kb
"""

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Главное меню бота (Reply клавиатура)
    Постоянно видна внизу экрана
    
    Кнопки:
    - 💬 Общение с AI — основной режим (чат с PandaPalAI)
    - 📚 Помощь с уроками — специализированная помощь
    - 📊 Мой прогресс — статистика и достижения
    - ⚙️ Настройки — профиль, возраст, класс
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура главного меню
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💬 Общение с AI"),
                KeyboardButton(text="📚 Помощь с уроками"),
            ],
            [
                KeyboardButton(text="📊 Мой прогресс"),
                KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True,  # Адаптивный размер кнопок
        one_time_keyboard=False,  # Клавиатура постоянно видна
        input_field_placeholder="Напиши сообщение или выбери действие..."
    )
    
    return keyboard


def get_subjects_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора предмета
    Inline кнопки для быстрого выбора
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с предметами
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔢 Математика", callback_data="subject:math"),
                InlineKeyboardButton(text="📖 Русский язык", callback_data="subject:russian"),
            ],
            [
                InlineKeyboardButton(text="🌍 Окружающий мир", callback_data="subject:world"),
                InlineKeyboardButton(text="🇬🇧 Английский", callback_data="subject:english"),
            ],
            [
                InlineKeyboardButton(text="⚗️ Химия", callback_data="subject:chemistry"),
                InlineKeyboardButton(text="🔬 Физика", callback_data="subject:physics"),
            ],
            [
                InlineKeyboardButton(text="📜 История", callback_data="subject:history"),
                InlineKeyboardButton(text="🌎 География", callback_data="subject:geography"),
            ],
            [
                InlineKeyboardButton(text="🎨 Другой предмет", callback_data="subject:other"),
            ],
        ]
    )
    
    return keyboard


def get_help_type_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора типа помощи
    
    Returns:
        InlineKeyboardMarkup: Типы помощи
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Решить задачу", callback_data="help:solve"),
            ],
            [
                InlineKeyboardButton(text="📚 Объяснить тему", callback_data="help:explain"),
            ],
            [
                InlineKeyboardButton(text="✅ Проверить ответ", callback_data="help:check"),
            ],
            [
                InlineKeyboardButton(text="💡 Дать подсказку", callback_data="help:hint"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main"),
            ],
        ]
    )
    
    return keyboard


def get_settings_keyboard(user_type: str = 'child') -> InlineKeyboardMarkup:
    """
    Клавиатура настроек профиля
    
    Args:
        user_type: Тип пользователя (child/parent/teacher)
    
    Returns:
        InlineKeyboardMarkup: Клавиатура настроек
    """
    buttons = [
        [
            InlineKeyboardButton(text="👤 Изменить имя", callback_data="settings:name"),
        ],
        [
            InlineKeyboardButton(text="🎂 Указать возраст", callback_data="settings:age"),
            InlineKeyboardButton(text="🎓 Указать класс", callback_data="settings:grade"),
        ],
    ]
    
    # Дополнительные настройки для родителей
    if user_type == 'parent':
        buttons.append([
            InlineKeyboardButton(
                text="👨‍👧 Связать с ребёнком", 
                callback_data="settings:link_child"
            ),
        ])
    
    # Кнопка очистки истории
    buttons.append([
        InlineKeyboardButton(text="🗑️ Очистить историю чата", callback_data="settings:clear_history"),
    ])
    
    # Кнопка назад
    buttons.append([
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="menu:main"),
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    return keyboard


def get_grade_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора класса (1-11)
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с классами
    """
    # Генерируем кнопки для классов 1-11
    buttons = []
    
    # Первая строка: 1-4 класс
    buttons.append([
        InlineKeyboardButton(text=f"{i} класс", callback_data=f"grade:{i}")
        for i in range(1, 5)
    ])
    
    # Вторая строка: 5-8 класс
    buttons.append([
        InlineKeyboardButton(text=f"{i} класс", callback_data=f"grade:{i}")
        for i in range(5, 9)
    ])
    
    # Третья строка: 9-11 класс
    buttons.append([
        InlineKeyboardButton(text=f"{i} класс", callback_data=f"grade:{i}")
        for i in range(9, 12)
    ])
    
    # Кнопка отмены
    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="menu:main"),
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    return keyboard


def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения действия
    
    Args:
        action: ID действия для callback_data
    
    Returns:
        InlineKeyboardMarkup: Кнопки подтверждения
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"confirm:{action}"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel:{action}"),
            ],
        ]
    )
    
    return keyboard

