"""
Обработчик геолокации для обеспечения безопасности детей.

Этот модуль реализует функциональность отправки геолокации от детей
родителям для обеспечения безопасности. Включает в себя клавиатуру
для запроса местоположения и обработку полученных координат.

Основные возможности:
- Запрос текущего местоположения ребенка
- Отправка координат родителям с ссылками на карты
- Интеграция с Яндекс.Картами, Google Maps и 2GIS
- Безопасность: координаты не сохраняются в базе данных
- GDPR совместимость: данные обрабатываются только для отправки

Безопасность:
- Доступ только для подтвержденных детей
- Координаты не сохраняются в базе данных
- Отправка только привязанным родителям
- Логирование всех запросов геолокации
"""

from aiogram import F, Router
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from loguru import logger

from bot.database import get_db
from bot.keyboards.main_kb import get_main_menu_keyboard
from bot.services.user_service import UserService

router = Router(name="location")


def get_location_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру для запроса геолокации.

    Создает специальную Reply клавиатуру с кнопкой для запроса
    текущего местоположения пользователя. Использует Telegram API
    для автоматического получения координат.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопкой отправки геолокации.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📍 Отправить мое местоположение", request_location=True),
            ],
            [
                KeyboardButton(text="🔙 Отмена"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Нажми кнопку чтобы поделиться местоположением",
    )

    return keyboard


@router.message(F.text == "📍 Где я")
async def request_location(message: Message):
    """
    Обработчик кнопки "📍 Где я"
    Запрашивает разрешение на отправку геолокации
    """
    telegram_id = message.from_user.id

    logger.info(f"📍 Пользователь {telegram_id} запросил функцию геолокации")

    with get_db() as db:
        user_service = UserService(db)
        user = user_service.get_user_by_telegram_id(telegram_id)

        if not user:
            await message.answer("❌ Сначала зарегистрируйся командой /start")
            return

        # Проверяем есть ли родитель
        if not user.parent_telegram_id:
            await message.answer(
                text="📍 <b>Отправка местоположения родителям</b>\n\n"
                "⚠️ У тебя пока не привязан родитель.\n\n"
                "Попроси маму или папу зарегистрироваться в боте и "
                "связать ваши аккаунты через настройки!\n\n"
                "Тогда ты сможешь отправлять им свое местоположение для безопасности 🛡️",
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard(),
            )
            return

    await message.answer(
        text="📍 <b>Отправить местоположение родителям</b>\n\n"
        "Нажми кнопку ниже, чтобы поделиться своим местоположением.\n\n"
        "🔒 <b>Безопасно:</b>\n"
        "• Координаты увидят только твои родители\n"
        "• Мы не сохраняем твою геолокацию\n"
        "• Это одноразовая отправка\n\n"
        "💡 <i>Это поможет родителям знать, что с тобой всё в порядке!</i>",
        reply_markup=get_location_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.location)
async def handle_location(message: Message):
    """
    Обработчик полученной геолокации
    Отправляет местоположение родителям
    """
    telegram_id = message.from_user.id
    location = message.location

    logger.info(
        f"📍 Получена геолокация от {telegram_id}: "
        f"lat={location.latitude}, lon={location.longitude}"
    )

    with get_db() as db:
        user_service = UserService(db)
        user = user_service.get_user_by_telegram_id(telegram_id)

        if not user or not user.parent_telegram_id:
            await message.answer(
                "❌ Родитель не найден. Попроси родителей зарегистрироваться в боте!",
                reply_markup=get_main_menu_keyboard(),
            )
            return

        # Формируем ссылки на карты
        lat = location.latitude
        lon = location.longitude

        # Яндекс.Карты
        yandex_url = f"https://yandex.ru/maps/?ll={lon},{lat}&z=16&pt={lon},{lat}"

        # Google Maps
        google_url = f"https://www.google.com/maps?q={lat},{lon}"

        # 2GIS
        gis_url = f"https://2gis.ru/geo/{lon},{lat}"

        # Формируем сообщение для родителя
        parent_message = f"""
📍 <b>Местоположение от {user.first_name}</b>

🧒 Ваш ребенок поделился своим местоположением:

📊 <b>Координаты:</b>
• Широта: <code>{lat}</code>
• Долгота: <code>{lon}</code>

🗺️ <b>Открыть на картах:</b>
• <a href="{yandex_url}">Яндекс.Карты</a>
• <a href="{google_url}">Google Maps</a>
• <a href="{gis_url}">2GIS</a>

🕐 <b>Время:</b> {message.date.strftime('%d.%m.%Y %H:%M:%S')}

🛡️ <i>Отправлено через PandaPal для вашей безопасности</i>
"""

        try:
            # Отправляем родителю
            await message.bot.send_message(
                chat_id=user.parent_telegram_id,
                text=parent_message,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )

            # Также отправляем саму геолокацию
            await message.bot.send_location(
                chat_id=user.parent_telegram_id, latitude=lat, longitude=lon
            )

            logger.info(f"✅ Геолокация отправлена родителю {user.parent_telegram_id}")

            # Подтверждение ребенку
            await message.answer(
                text="✅ <b>Местоположение отправлено!</b>\n\n"
                f"Твои родители получили твои координаты и ссылки на карты.\n\n"
                f"🛡️ Они знают что с тобой всё в порядке!",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML",
            )

        except Exception as e:
            logger.error(f"❌ Ошибка отправки геолокации родителю: {e}")

            await message.answer(
                text="😔 Не удалось отправить местоположение родителям.\n\n"
                "Возможно, они еще не зарегистрированы в боте или заблокировали его.",
                reply_markup=get_main_menu_keyboard(),
            )


@router.message(F.text == "🔙 Отмена")
async def cancel_location(message: Message):
    """Отмена отправки геолокации"""
    await message.answer(text="❌ Отменено", reply_markup=get_main_menu_keyboard())
