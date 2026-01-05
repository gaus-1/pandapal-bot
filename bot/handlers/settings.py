"""
Обработчики настроек пользователя для персонализации бота.

Этот модуль реализует функциональность настройки профиля пользователя,
включая изменение возраста, класса и других параметров для адаптации
ботов под индивидуальные потребности каждого пользователя.

Основные возможности:
- Изменение возраста пользователя (6-18 лет)
- Выбор класса обучения (1-11 класс)
- Настройка профиля пользователя
- Очистка истории чата
- Сброс настроек к значениям по умолчанию

Состояния FSM:
- waiting_for_age: Ожидание ввода возраста
- waiting_for_grade: Ожидание выбора класса

Все изменения сохраняются в базе данных и влияют на
адаптацию ответов AI под возраст и уровень пользователя.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.database import get_db
from bot.keyboards.main_kb import (
    get_confirm_keyboard,
    get_grade_selection_keyboard,
    get_main_menu_keyboard,
    get_settings_keyboard,
)
from bot.services import ChatHistoryService, UserService

# Создаём роутер
router = Router(name="settings")


# Состояния для FSM (Finite State Machine)
class SettingsStates(StatesGroup):
    """Состояния диалога настроек"""

    waiting_for_age = State()  # Ожидание ввода возраста
    waiting_for_name = State()  # Ожидание ввода имени


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    """
    Показать меню настроек

    Args:
        message: Сообщение с кнопкой "Настройки"
    """
    telegram_id = message.from_user.id

    with get_db() as db:
        user_service = UserService(db)
        user = user_service.get_user_by_telegram_id(telegram_id)

        if not user:
            await message.answer("❌ Пользователь не найден. Нажми /start")
            return

        # Формируем информацию о профиле
        user_type_display = "Ученик"

        profile_info = f"""
⚙️ <b>Настройки профиля</b>

👤 Имя: {user.first_name or 'Не указано'}
🎂 Возраст: {user.age or 'Не указан'}
🎓 Класс: {user.grade or 'Не указан'}
📊 Тип: {user_type_display}

Выбери, что хочешь изменить:
"""
        await message.answer(
            text=profile_info,
            reply_markup=get_settings_keyboard(user.user_type),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "settings:age")
async def settings_age(callback: CallbackQuery, state: FSMContext):
    """
    Начать изменение возраста

    Args:
        callback: Callback от inline кнопки
        state: FSM состояние
    """
    await callback.message.edit_text(
        text="🎂 <b>Сколько тебе лет?</b>\n\n" "Напиши свой возраст цифрами (например: 10)",
        parse_mode="HTML",
    )

    # Переводим в состояние ожидания возраста
    await state.set_state(SettingsStates.waiting_for_age)
    await callback.answer()


@router.message(SettingsStates.waiting_for_age, F.text)
async def process_age(message: Message, state: FSMContext):
    """
    Обработка введённого возраста

    Args:
        message: Сообщение с возрастом
        state: FSM состояние
    """
    try:
        age = int(message.text.strip())

        # Валидация возраста
        if age < 6 or age > 18:
            await message.answer("❌ Возраст должен быть от 6 до 18 лет.\n" "Попробуй ещё раз:")
            return

        # Сохраняем возраст в БД
        with get_db() as db:
            user_service = UserService(db)
            user_service.update_user_profile(telegram_id=message.from_user.id, age=age)

        await message.answer(
            text=f"✅ Отлично! Запомнил, что тебе {age} лет.\n\n" "Теперь укажи свой класс:",
            reply_markup=get_grade_selection_keyboard(),
        )

        # Очищаем состояние
        await state.clear()

    except ValueError:
        await message.answer("❌ Пожалуйста, введи возраст цифрами (например: 10)")


@router.callback_query(F.data.startswith("grade:"))
async def set_grade(callback: CallbackQuery):
    """
    Установить класс пользователя

    Args:
        callback: Callback с данными класса
    """
    # Извлекаем номер класса из callback_data
    grade = int(callback.data.split(":")[1])

    telegram_id = callback.from_user.id

    # Сохраняем в БД
    with get_db() as db:
        user_service = UserService(db)
        user_service.update_user_profile(telegram_id=telegram_id, grade=grade)

    await callback.message.edit_text(
        text=f"✅ Отлично! Ты учишься в {grade} классе.\n\n"
        f"Теперь я буду адаптировать объяснения под программу {grade} класса! 📚\n\n"
        f"Готов помогать с учёбой! Задавай любые вопросы 🐼",
        reply_markup=None,
    )

    # Показываем главное меню
    await callback.message.answer(text="Выбери действие:", reply_markup=get_main_menu_keyboard())

    await callback.answer("Профиль обновлён!")


@router.callback_query(F.data == "settings:clear_history")
async def confirm_clear_history(callback: CallbackQuery):
    """
    Запрос подтверждения очистки истории

    Args:
        callback: Callback от кнопки
    """
    await callback.message.edit_text(
        text="⚠️ <b>Очистить историю чата?</b>\n\n"
        "Я забуду наш разговор и не смогу ссылаться на предыдущие сообщения.\n\n"
        "Ты уверен?",
        reply_markup=get_confirm_keyboard("clear_history"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "confirm:clear_history")
async def clear_chat_history(callback: CallbackQuery):
    """
    Очистка истории чата

    Args:
        callback: Callback подтверждения
    """
    telegram_id = callback.from_user.id

    with get_db() as db:
        history_service = ChatHistoryService(db)
        deleted_count = history_service.clear_history(telegram_id)

    await callback.message.edit_text(
        text=f"✅ История очищена!\n\n"
        f"Удалено {deleted_count} сообщений.\n"
        f"Начнём общение с чистого листа! 🐼",
        reply_markup=None,
    )

    await callback.answer("История очищена")

    logger.info(f"🗑️ Очищена история для {telegram_id}: {deleted_count} сообщений")


@router.callback_query(F.data.startswith("cancel:"))
async def cancel_action(callback: CallbackQuery):
    """
    Отмена действия

    Args:
        callback: Callback от кнопки "Нет"
    """
    await callback.message.edit_text(text="Действие отменено.", reply_markup=None)
    await callback.answer()


@router.callback_query(F.data == "menu:main")
async def show_main_menu(callback: CallbackQuery):
    """
    Вернуться в главное меню

    Args:
        callback: Callback от кнопки "Назад"
    """
    await callback.message.edit_text(text="Главное меню:", reply_markup=None)

    await callback.message.answer(text="Выбери действие:", reply_markup=get_main_menu_keyboard())

    await callback.answer()
