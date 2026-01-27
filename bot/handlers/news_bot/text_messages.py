"""
Обработчик обычных текстовых сообщений для новостного бота.

Отвечает пользователю, если он написал что-то, что не является командой.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

router = Router(name="news_bot_text_messages")


def register_handlers(router_instance: Router) -> None:
    """Зарегистрировать handlers в роутере."""
    router_instance.message.register(handle_text_message, F.text)


async def handle_text_message(message: Message, state: FSMContext) -> None:
    """
    Обработчик обычных текстовых сообщений.

    Отвечает пользователю, если он написал что-то, что не является командой.
    """
    telegram_id = message.from_user.id
    text = message.text or ""

    logger.info(f"📰 Текстовое сообщение в новостном боте: user={telegram_id}, text={text[:50]}")

    # Проверяем текущее состояние
    current_state = await state.get_state()
    logger.debug(f"📰 Текущее состояние FSM: {current_state}")

    # Если пользователь в процессе настройки, игнорируем текстовые сообщения
    # (настройка идет через кнопки)
    if current_state in ("news_setting_age", "news_setting_grade", "news_selecting_categories"):
        logger.debug(f"📰 Игнорируем текстовое сообщение в состоянии {current_state}")
        return

    # Для обычных текстовых сообщений предлагаем использовать команды
    help_text = (
        "👋 Привет! Я PandaPal News — бот с интересными новостями для детей!\n\n"
        "Используй команды:\n"
        "/start — приветствие и настройка\n"
        "/news — последние новости\n"
        "/categories — выбор категорий\n"
        "/settings — настройки\n"
        "/help — справка"
    )

    try:
        await message.answer(help_text)
        logger.info(f"📰 Ответ отправлен пользователю {telegram_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки ответа пользователю {telegram_id}: {e}", exc_info=True)
