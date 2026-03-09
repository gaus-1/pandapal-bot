"""
Вспомогательные функции для AI чата.
"""

import re

from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from loguru import logger

# Клавиатура для перехода к Premium
PREMIUM_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💎 Узнать о Premium", callback_data="premium:info")]
    ]
)


async def check_premium_limit(telegram_id: int, username: str | None, message: Message) -> bool:
    """
    Проверка Premium-лимитов перед AI-запросом.

    Returns:
        True если запрос разрешен, False если заблокирован (ответ уже отправлен).
    """
    from bot.database import get_db
    from bot.services import UserService
    from bot.services.premium_features_service import PremiumFeaturesService

    with get_db() as db:
        user_service = UserService(db)
        premium_service = PremiumFeaturesService(db)
        user = user_service.get_user_by_telegram_id(telegram_id)
        if user:
            can_request, limit_reason = premium_service.can_make_ai_request(
                telegram_id, username=username
            )
            if not can_request:
                logger.warning(f"🚫 AI запрос заблокирован для user={telegram_id}: {limit_reason}")
                await message.answer(limit_reason, reply_markup=PREMIUM_KEYBOARD, parse_mode="HTML")
                return False
    return True


def read_file_safely(
    file_obj, max_size: int = 20 * 1024 * 1024, chunk_size: int = 64 * 1024
) -> bytes:
    """
    Потоковое чтение файла с ограничением размера.

    Читает файл по частям (chunks) вместо загрузки всего в память.
    Это критично для больших файлов (голос, аудио, изображения).

    Args:
        file_obj: Файловый объект (BytesIO или подобный) с методом read()
        max_size: Максимальный размер файла в байтах (по умолчанию 20MB)
        chunk_size: Размер чанка для чтения (по умолчанию 64KB)

    Returns:
        bytes: Содержимое файла

    Raises:
        ValueError: Если файл превышает max_size
    """
    data = b""
    total_read = 0

    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break

        data += chunk
        total_read += len(chunk)

        if total_read > max_size:
            raise ValueError(
                f"Файл слишком большой: {total_read} байт > {max_size} байт "
                f"({max_size / (1024 * 1024):.1f}MB)"
            )

    return data


def extract_user_name_from_message(user_message: str) -> tuple[str | None, bool]:
    """
    Извлечение имени пользователя из сообщения.

    Returns:
        tuple: (имя или None, является ли отказом)
    """
    from bot.utils.chat_utils import extract_user_name_from_message as _extract

    return _extract(user_message)


# Ключевые слова для детектирования запроса на генерацию изображений
_IMAGE_GENERATION_KEYWORDS = [
    "нарисуй",
    "нарисовать",
    "рисунок",
    "картинк",
    "изображени",
    "фото",
    "иллюстраци",
    "визуализируй",
    "покажи как выглядит",
    "сгенерируй изображение",
    "создай картинку",
]


async def handle_image_generation_request(
    message: Message,
    user_message: str,
    state: FSMContext,  # noqa: ARG001
) -> bool:
    """
    Обработка запроса на генерацию изображения через YandexART.

    Сначала проверяет, не является ли запрос учебной визуализацией.
    Если нет — проверяет наличие ключевых слов генерации изображений.

    Returns:
        True если запрос обработан (ответ отправлен), False — продолжить обработку.
    """
    from bot.services.visualization_service import get_visualization_service

    viz_service = get_visualization_service()
    visualization_image, _ = viz_service.detect_visualization_request(user_message)

    # Если это учебная визуализация — не перехватываем, пусть основной обработчик решает
    if visualization_image:
        return False

    is_image_request = any(kw in user_message.lower() for kw in _IMAGE_GENERATION_KEYWORDS)
    telegram_id = message.from_user.id

    logger.debug(
        f"🎨 Проверка детектора изображений: '{user_message[:50]}', "
        f"is_image_request={is_image_request}"
    )

    if is_image_request:
        from bot.services.yandex_art_service import get_yandex_art_service

        art_service = get_yandex_art_service()
        is_available = art_service.is_available()

        logger.info(
            f"🎨 Запрос на генерацию изображения (не учебный) от {telegram_id}: "
            f"'{user_message[:50]}', art_service.is_available={is_available}"
        )

        if is_available:
            try:
                image_bytes = await art_service.generate_image(
                    prompt=user_message, style="auto", aspect_ratio="1:1"
                )

                if image_bytes:
                    photo = BufferedInputFile(image_bytes, filename="generated_image.jpg")
                    caption = "Могу нарисовать что-то по школьным предметам! 📚"
                    await message.answer_photo(photo=photo, caption=caption)
                    logger.info(f"🎨 Изображение сгенерировано для пользователя {telegram_id}")

                    from bot.database import get_db
                    from bot.services import ChatHistoryService

                    with get_db() as db:
                        history_service = ChatHistoryService(db)
                        history_service.add_message(
                            telegram_id=telegram_id,
                            message_text=user_message,
                            message_type="user",
                        )
                        history_service.add_message(
                            telegram_id=telegram_id,
                            message_text=caption,
                            message_type="ai",
                        )
                    return True
                else:
                    logger.warning(f"⚠️ Не удалось сгенерировать изображение для {telegram_id}")
                    await message.answer(
                        "Извини, не получилось нарисовать картинку. "
                        "Попробуй переформулировать запрос!"
                    )
                    return True

            except Exception as e:
                logger.error(f"❌ Ошибка генерации изображения: {e}", exc_info=True)
                await message.answer("Упс, что-то пошло не так с рисованием. Попробуй снова!")
                return True
    else:
        logger.warning(
            f"⚠️ YandexART недоступен (нет API ключей или роли). " f"Запрос: '{user_message[:50]}'"
        )
        logger.info("📝 Обрабатываем запрос как обычный текст")

    return False


async def detect_and_translate_message(user_message: str) -> tuple[str, str | None]:
    """
    Определение языка текста и перевод на русский при необходимости.

    Returns:
        (модифицированное_сообщение, код_языка или None)
    """
    from bot.services.translate_service import get_translate_service

    translate_service = get_translate_service()
    detected_lang = await translate_service.detect_language(user_message)

    if (
        not detected_lang
        or detected_lang == "ru"
        or detected_lang not in translate_service.SUPPORTED_LANGUAGES
    ):
        return user_message, None

    logger.info(f"🌍 Обнаружен иностранный язык: {detected_lang}")
    translated_text = await translate_service.translate_text(
        user_message, target_language="ru", source_language=detected_lang
    )

    if translated_text:
        lang_name = translate_service.get_language_name(detected_lang)
        modified_message = (
            f"🌍 Вижу, что ты написал на {lang_name}!\n\n"
            f"📝 Оригинал: {user_message}\n"
            f"🇷🇺 Перевод: {translated_text}\n\n"
            f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
        )
        logger.info(f"✅ Текст переведен: {detected_lang} → ru")
        return modified_message, detected_lang

    return user_message, detected_lang


# Названия типов диаграмм для расширенных сообщений
_DIAGRAM_NAMES: dict[str, str] = {
    "bar": "столбчатую диаграмму",
    "pie": "круговую диаграмму",
    "line": "линейный график",
    "histogram": "гистограмму",
    "scatter": "диаграмму рассеяния",
    "box": "ящик с усами",
    "bubble": "пузырьковую диаграмму",
    "heatmap": "тепловую карту",
}


def build_visualization_enhanced_message(
    user_message: str,
    viz_type: str,
) -> str:
    """
    Построение расширенного сообщения с контекстом визуализации для AI.

    Добавляет инструкции для AI, чтобы сгенерировать релевантное пояснение
    к визуализации (таблице, графику, карте и т.д.).

    Returns:
        Расширенное сообщение с контекстом визуализации.
    """
    _common = (
        " Развёрнутое пояснение: что изображено, как читать. "
        "Не менее 10 примеров или пунктов по теме визуала. "
        "В конце один вовлекающий вопрос (Понятно? Хочешь разобрать ещё? Есть вопросы?). "
    )
    if viz_type == "multiplication_table":
        return (
            f"{user_message}\n\n"
            "Дай исчерпывающее глубокое пояснение про таблицу умножения: "
            "как её использовать, для чего нужна, как читать. "
            "Не перечисляй все значения текстом — таблица уже показана. "
            f"Не менее 10 примеров использования (например 5×3, 7×4 и т.д.).{_common}"
        )

    if viz_type == "graph":
        return (
            f"{user_message}\n\n"
            "Дай исчерпывающее пояснение про этот график: "
            "что показывает, как читать, свойства (возрастает/убывает, нули, экстремумы). "
            f"Не менее 10 конкретных примеров по точкам или участкам графика.{_common}"
        )

    if viz_type in _DIAGRAM_NAMES:
        diagram_name = _DIAGRAM_NAMES[viz_type]
        return (
            f"{user_message}\n\n"
            f"Дай исчерпывающее пояснение про {diagram_name}: "
            f"что показывает, как читать и использовать. Не дублируй визуализацию текстом. "
            f"Не менее 10 примеров или пунктов.{_common}"
        )

    if viz_type == "map":
        return (
            f"{user_message}\n\n"
            "Дай исчерпывающее пояснение про карту: "
            "что показано, где объект, географические особенности, соседи, объекты. "
            f"Не менее 10 примеров или фактов по карте.{_common}"
        )

    return (
        f"{user_message}\n\n"
        "Дай исчерпывающее пояснение по теме запроса: что изображено, как использовать. "
        f"Не менее 10 примеров или пунктов.{_common}"
    )


# Паттерны для удаления упоминаний автоматической генерации из ответа AI
_AUTO_GENERATION_PATTERNS = [
    r"(?:систем[аеы]?\s+)?автоматически\s+сгенериру[ею]т?\s+[^.!?\n]*",
    r"покажу\s+(?:график|таблиц[ау]|карт[ау]|диаграмм[ау]|схем[ау]).*?систем[аеы]?\s+автоматически",
    r"автоматически\s+создан[аоы]?\s+[^.!?\n]*",
    r"создан[аоы]?\s+автоматически[^.!?\n]*",
    r"генерируется\s+автоматически[^.!?\n]*",
    r"автоматическая\s+генерация[^.!?\n]*",
    r"сгенерирован[аоы]?\s+автоматически[^.!?\n]*",
    r"\[Сгенерирован[аоы]?\s+[^\]]+\]",
    r"\(Сгенерирован[аоы]?\s+[^\)]+\)",
    r"\[Создан[аоы]?\s+автоматически[^\]]*\]",
    r"Эт[аои][тй]?\s+(?:карт[ау]|график|таблиц[ау]|диаграмм[ау]|схем[ау]|изображени[ея]?)"
    r"\s+был[аоы]?\s+(?:создан[аоы]?|сгенерирован[аоы]?)[^.!?\n]*",
    r"владельцем\s+сайт[аа]?[^.!?\n]*",
    r"на\s+основе\s+данных[^.!?\n]*",
    r"создан[аоы]?\s+(?:автоматически\s+)?владельцем[^.!?\n]*",
    r"карт[ау]\s+(?:был[аоы]?\s+)?создан[аоы]?\s+автоматически[^.!?\n]*",
    r"карт[ау]\s+(?:был[аоы]?\s+)?сгенерирован[аоы]?\s+автоматически[^.!?\n]*",
    r"систем[аеы]?\s+(?:покажет|создаст|добавит|сгенерирует)[^.!?\n]*",
    r"(?:будет\s+)?показан[аоы]?\s+автоматически[^.!?\n]*",
]


def clean_auto_generation_mentions(response_text: str) -> str:
    """
    Удаление упоминаний автоматической генерации из ответа AI.

    Убирает фразы вроде «автоматически сгенерировано», «создано системой» и т.п.,
    которые AI иногда добавляет при наличии визуализации.
    """
    for pattern in _AUTO_GENERATION_PATTERNS:
        response_text = re.sub(pattern, "", response_text, flags=re.IGNORECASE)
    response_text = re.sub(r"\s+", " ", response_text)
    response_text = re.sub(r"\n\s*\n", "\n", response_text)
    return response_text.strip()


async def send_ai_response(
    message: Message,
    response_text: str,
    viz_result: bytes | None,
    viz_type: str | None,  # noqa: ARG001
    user_message: str = "",
) -> None:
    """
    Отправка ответа AI пользователю с опциональной визуализацией.

    Если есть визуализация — отправляет фото + текст (caption до 1024 символов).
    Иначе — текст, с кнопкой карты для географических вопросов.
    """
    if viz_result:
        photo = BufferedInputFile(viz_result, filename="visualization.png")
        await message.answer_photo(
            photo=photo,
            caption=response_text[:1024],
        )
        if len(response_text) > 1024:
            await message.answer(text=response_text[1024:])
    else:
        from bot.services.visualization_service import get_visualization_service

        viz_service = get_visualization_service()
        geo_location = viz_service.detect_geography_question(user_message)
        if geo_location:
            map_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🗺️ Показать карту",
                            callback_data=f"show_map:{geo_location[:50]}",
                        )
                    ]
                ]
            )
            await message.answer(text=response_text, reply_markup=map_keyboard)
        else:
            await message.answer(text=response_text)


async def offer_feedback_form(message: Message, request_count: int) -> None:
    """Предложение формы обратной связи каждые 20 сообщений."""
    if request_count % 20 == 0 and request_count > 0:
        feedback_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 Оставить отзыв",
                        url="https://forms.yandex.ru/cloud/695ba5a6068ff07700f0029a",
                    )
                ]
            ]
        )

        await message.answer(
            "🎉 Спасибо за общение! Поделись мнением?\n" "Твой отзыв поможет улучшить PandaPal 🐼",
            reply_markup=feedback_keyboard,
        )
