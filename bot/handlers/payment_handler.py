"""
Обработчик платежей через Telegram.

- Stars: только донаты (donation_*). Premium по Stars НЕ даётся.
- Premium: только при реальной оплате 299 ₽ через кнопку в разделе Премиум (ЮKassa).
"""

from aiogram import Router
from aiogram.types import Message, PreCheckoutQuery, SuccessfulPayment
from loguru import logger

# Создаём роутер для обработчиков платежей
router = Router(name="payment")


@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    """
    Обработчик PreCheckoutQuery - подтверждение платежа перед оплатой.

    Telegram отправляет этот запрос перед показом формы оплаты.
    Нужно ответить ok=True чтобы разрешить оплату.

    Args:
        query: Объект PreCheckoutQuery от Telegram
    """
    try:
        # Валидация суммы: минимум 1 Star, максимум 10000 Stars
        if query.total_amount is not None and (
            query.total_amount < 1 or query.total_amount > 10000
        ):
            logger.warning(
                f"⚠️ Подозрительная сумма платежа: {query.total_amount} от user={query.from_user.id}"
            )
            await query.answer(ok=False, error_message="Некорректная сумма платежа")
            return

        # Разрешаем донаты (payload начинается с "donation_")
        if query.invoice_payload and query.invoice_payload.startswith("donation_"):
            logger.info(f"💝 PreCheckout для доната: user={query.from_user.id}")
            await query.answer(ok=True)
            return

        # Premium по Stars не даём — только оплата 299 ₽ в разделе Премиум (ЮKassa)
        if query.invoice_payload and query.invoice_payload.startswith("premium_"):
            logger.info(
                f"⚠️ PreCheckout premium_* отклонён: Stars не дают Premium. user={query.from_user.id}"
            )
            await query.answer(
                ok=False,
                error_message="Premium только по оплате 299 ₽ в разделе Премиум (кнопка в боте).",
            )
            return

        if not query.invoice_payload or not query.invoice_payload.startswith("donation_"):
            logger.warning(f"⚠️ Неизвестный invoice payload: {query.invoice_payload}")
            await query.answer(ok=False, error_message="Неизвестный тип платежа")
            return

        await query.answer(ok=True)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки PreCheckoutQuery: {e}")
        await query.answer(ok=False, error_message="Ошибка обработки платежа")


@router.message(SuccessfulPayment)
async def successful_payment_handler(message: Message):
    """
    Обработчик успешной оплаты (Telegram).

    Донаты (Stars) — благодарим. Premium по Stars не активируется;
    Premium только при оплате 299 ₽ через ЮKassa (раздел Премиум).

    Args:
        message: Сообщение с данными об успешной оплате
    """
    try:
        payment: SuccessfulPayment = message.successful_payment

        # Обрабатываем донаты (payload начинается с "donation_")
        if payment.invoice_payload and payment.invoice_payload.startswith("donation_"):
            # Это донат, не Premium подписка
            logger.info(
                f"💝 Донат получен: user={message.from_user.id}, "
                f"amount={payment.total_amount}, currency={payment.currency}"
            )

            # Переводим звезды на @SavinVE (админ)
            # Telegram Stars нельзя напрямую перевести через API,
            # но можно использовать внутренний механизм бота
            try:
                from bot.config import settings

                admin_username = settings.get_admin_usernames_list()[0]  # Первый админ
                # Примечание: Telegram не предоставляет API для прямого перевода Stars
                # Звезды остаются у бота, но можно логировать для ручного перевода
                logger.info(
                    f"💝 Донат {payment.total_amount} Stars от {message.from_user.id} "
                    f"(требуется ручной перевод на @{admin_username})"
                )
            except Exception as e:
                logger.warning(f"⚠️ Ошибка получения админа для перевода звезд: {e}")

            await message.answer(
                "💝 <b>Спасибо за поддержку проекта PandaPal!</b>\n\n"
                "Твоя поддержка помогает развитию бота и улучшению качества обучения для всех детей! 🎉",
                parse_mode="HTML",
            )
            return

        # Платёж Stars с payload premium_* — НЕ активируем Premium (только 299 ₽ через ЮKassa)
        if payment.invoice_payload and payment.invoice_payload.startswith("premium_"):
            logger.info(
                f"⚠️ SuccessfulPayment premium_* проигнорирован для активации: "
                f"Stars не дают Premium. user={message.from_user.id}"
            )
            await message.answer(
                "💎 <b>Premium по Stars не активируется.</b>\n\n"
                "Premium можно оформить только по оплате 299 ₽ через кнопку в разделе <b>Премиум</b> в боте.",
                parse_mode="HTML",
            )
            return

    except Exception as e:
        # Используем % для логирования чтобы избежать проблем с фигурными скобками в SQL
        logger.error("❌ Критическая ошибка активации Premium: %s", str(e), exc_info=True)
        try:
            await message.answer(
                "❌ Произошла ошибка при активации Premium. "
                "Мы уже работаем над исправлением. Обратитесь в поддержку."
            )
        except Exception as send_error:
            logger.warning("⚠️ Не удалось отправить сообщение об ошибке: %s", send_error)
