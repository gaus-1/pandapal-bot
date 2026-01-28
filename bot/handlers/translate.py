"""
Обработчик команды /translate для изучения иностранных языков.

Использует Yandex Translate API для перевода текста.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from loguru import logger

from bot.services.translate_service import get_translate_service

router = Router()


class TranslateStates(StatesGroup):
    """Состояния для процесса перевода."""

    waiting_for_text = State()


@router.message(Command("translate"))
async def translate_command(message: Message, state: FSMContext):  # noqa: ARG001
    """Команда для перевода текста."""
    # Клавиатура с выбором языка
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇬🇧 Английский → Русский", callback_data="translate_en_ru"
                ),
                InlineKeyboardButton(
                    text="🇷🇺 Русский → Английский", callback_data="translate_ru_en"
                ),
            ],
            [
                InlineKeyboardButton(text="🇩🇪 Немецкий → Русский", callback_data="translate_de_ru"),
                InlineKeyboardButton(
                    text="🇫🇷 Французский → Русский", callback_data="translate_fr_ru"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🇪🇸 Испанский → Русский", callback_data="translate_es_ru"
                ),
            ],
        ]
    )

    await message.answer(
        "🌍 <b>Переводчик PandaPal</b>\n\n" "Выбери направление перевода:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(lambda c: c.data and c.data.startswith("translate_"))
async def handle_translate_language_choice(callback_query, state: FSMContext):
    """Обработка выбора языка для перевода."""
    data = callback_query.data.split("_")
    from_lang = data[1]
    to_lang = data[2]

    # Сохраняем выбранные языки
    await state.update_data(from_lang=from_lang, to_lang=to_lang)
    await state.set_state(TranslateStates.waiting_for_text)

    # Получаем названия языков
    translate_service = get_translate_service()
    from_lang_name = translate_service.get_language_name(from_lang)
    to_lang_name = translate_service.get_language_name(to_lang)

    await callback_query.message.edit_text(
        f"📝 Отлично! Теперь отправь текст для перевода:\n"
        f"{from_lang_name} → {to_lang_name}\n\n"
        f"Например: слово, фразу или целое предложение"
    )

    await callback_query.answer()


@router.message(TranslateStates.waiting_for_text)
async def handle_translate_text(message: Message, state: FSMContext):
    """Обработка текста для перевода."""
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        from_lang = data.get("from_lang")
        to_lang = data.get("to_lang")

        if not from_lang or not to_lang:
            await message.answer("❌ Ошибка: язык не выбран. Начни заново с /translate")
            await state.clear()
            return

        text_to_translate = message.text

        if not text_to_translate or len(text_to_translate) > 1000:
            await message.answer(
                "❌ Текст слишком длинный или пустой. Максимум 1000 символов.\n"
                "Попробуй еще раз или /translate для начала заново."
            )
            return

        # Показываем что переводим
        processing_msg = await message.answer("🔄 Перевожу... Подожди! 🐼")

        # Получаем сервис перевода
        translate_service = get_translate_service()

        # Переводим текст
        translated_text = await translate_service.translate_text(
            text=text_to_translate, target_language=to_lang, source_language=from_lang
        )

        if not translated_text:
            await processing_msg.edit_text(
                "❌ Не удалось перевести текст. Попробуй еще раз или /translate"
            )
            return

        # Получаем названия языков
        from_lang_name = translate_service.get_language_name(from_lang)
        to_lang_name = translate_service.get_language_name(to_lang)

        # Форматируем ответ
        response = (
            f"🌍 <b>Перевод</b>\n\n"
            f"<b>{from_lang_name}:</b>\n{text_to_translate}\n\n"
            f"<b>{to_lang_name}:</b>\n{translated_text}\n\n"
            f"💡 Отправь еще текст для перевода или /translate для смены языка"
        )

        await processing_msg.edit_text(response, parse_mode="HTML")

        # Логируем перевод
        logger.info(
            f"✅ Перевод выполнен: {from_lang}→{to_lang}, "
            f"user={message.from_user.id}, text_len={len(text_to_translate)}"
        )

    except Exception as e:
        logger.error(f"❌ Ошибка перевода: {e}")
        await message.answer("❌ Произошла ошибка при переводе. Попробуй еще раз или /translate")
        await state.clear()
