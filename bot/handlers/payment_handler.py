"""
Обработчик платежей через Telegram Stars для Premium подписки.

Обрабатывает события от Telegram:
- PreCheckoutQuery: подтверждение платежа перед оплатой
- SuccessfulPayment: успешная оплата и активация подписки
"""

import re
from datetime import datetime

from aiogram import Router
from aiogram.types import Message, PreCheckoutQuery, SuccessfulPayment
from loguru import logger

from bot.database import get_db
from bot.services import SubscriptionService, UserService

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
        # Разрешаем донаты (payload начинается с "donation_")
        if query.invoice_payload and query.invoice_payload.startswith("donation_"):
            logger.info(f"💝 PreCheckout для доната: user={query.from_user.id}")
            await query.answer(ok=True)
            return

        # Обрабатываем только Premium подписки
        if not query.invoice_payload or not query.invoice_payload.startswith("premium_"):
            logger.warning(f"⚠️ Неизвестный invoice payload: {query.invoice_payload}")
            await query.answer(ok=False, error_message="Неизвестный тип платежа")
            return

        # Парсим payload: "premium_{plan_id}_{telegram_id}"
        # Пример: "premium_month_123456789"
        match = re.match(r"premium_(\w+)_(\d+)", query.invoice_payload)
        if not match:
            logger.warning(f"⚠️ Неверный формат payload: {query.invoice_payload}")
            await query.answer(ok=False, error_message="Неверный формат платежа")
            return

        plan_id = match.group(1)
        telegram_id = int(match.group(2))

        # Проверяем что пользователь существует
        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                logger.warning(f"⚠️ Пользователь не найден: {telegram_id}")
                await query.answer(ok=False, error_message="Пользователь не найден")
                return

            # Проверяем валидность плана
            valid_plans = ["week", "month", "year"]
            if plan_id not in valid_plans:
                logger.warning(f"⚠️ Неверный plan_id: {plan_id}")
                await query.answer(ok=False, error_message="Неверный тарифный план")
                return

        # Все проверки пройдены - разрешаем оплату
        logger.info(f"✅ PreCheckout подтвержден: user={telegram_id}, plan={plan_id}")
        await query.answer(ok=True)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки PreCheckoutQuery: {e}")
        await query.answer(ok=False, error_message="Ошибка обработки платежа")


@router.message(SuccessfulPayment)
async def successful_payment_handler(message: Message):
    """
    Обработчик успешной оплаты - активация Premium подписки.

    Telegram отправляет это сообщение после успешной оплаты.
    Нужно активировать подписку в БД.

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
            await message.answer(
                "💝 <b>Спасибо за поддержку проекта PandaPal!</b>\n\n"
                "Твоя поддержка помогает развитию бота и улучшению качества обучения для всех детей! 🎉",
                parse_mode="HTML",
            )
            return

        # Обрабатываем только Premium подписки
        if not payment.invoice_payload or not payment.invoice_payload.startswith("premium_"):
            logger.warning(f"⚠️ Неизвестный invoice payload в платеже: {payment.invoice_payload}")
            return

        # Парсим payload: "premium_{plan_id}_{telegram_id}"
        match = re.match(r"premium_(\w+)_(\d+)", payment.invoice_payload)
        if not match:
            logger.error(f"❌ Неверный формат payload: {payment.invoice_payload}")
            return

        plan_id = match.group(1)
        telegram_id = int(match.group(2))

        # Активируем подписку
        with get_db() as db:
            subscription_service = SubscriptionService(db)
            user_service = UserService(db)

            # Проверяем что пользователь существует
            user = user_service.get_user_by_telegram_id(telegram_id)
            if not user:
                logger.error(f"❌ Пользователь не найден при активации: {telegram_id}")
                await message.answer("❌ Ошибка: пользователь не найден. Обратитесь в поддержку.")
                return

            # Активируем подписку (Telegram Stars)
            subscription = subscription_service.activate_subscription(
                telegram_id=telegram_id,
                plan_id=plan_id,
                transaction_id=payment.telegram_payment_charge_id,
                invoice_payload=payment.invoice_payload,
                payment_method="stars",
                payment_id=payment.telegram_payment_charge_id,
            )

            db.commit()

            # Определяем длительность для сообщения
            plan_names = {
                "week": "неделю",
                "month": "месяц",
                "year": "год",
            }
            duration = plan_names.get(plan_id, plan_id)

            # Отправляем подтверждение
            await message.answer(
                f"🎉 <b>Premium активирован!</b>\n\n"
                f"✅ Подписка на {duration} успешно активирована.\n"
                f"📅 Действует до: {subscription.expires_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Теперь у тебя есть доступ ко всем Premium функциям!",
                parse_mode="HTML",
            )

            logger.info(
                f"💰 Premium активирован: user={telegram_id}, plan={plan_id}, "
                f"tx={payment.telegram_payment_charge_id}, expires={subscription.expires_at}"
            )

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
