"""
Обработчик команды /feedback для сбора обратной связи.

Интегрирован с Yandex Forms для структурированного сбора отзывов
от пользователей о качестве работы бота PandaPal.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

router = Router()

FEEDBACK_FORM_URL = "https://forms.yandex.ru/cloud/695ba5a6068ff07700f0029a"


@router.message(Command("feedback"))
async def feedback_command(message: Message):
    """Отправляет форму обратной связи."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📝 Оставить отзыв", url=FEEDBACK_FORM_URL)]]
    )

    await message.answer(
        "🐼 <b>Помоги улучшить PandaPal!</b>\n\n"
        "Пройди короткий опрос — это займёт 1 минуту 🙏\n"
        "Твоё мнение очень важно для нас!",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
