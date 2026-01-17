"""
Premium endpoints - Обработка платежей через ЮKassa
"""

import asyncio
import random
import uuid
from datetime import UTC

from aiohttp import web
from loguru import logger
from pydantic import ValidationError

from bot.api.validators import (
    PremiumPaymentRequest,
    PremiumYooKassaRequest,
    validate_telegram_id,
)
from bot.config import settings
from bot.database import get_db
from bot.models import Payment as PaymentModel
from bot.services import PaymentService, SubscriptionService, UserService


async def create_donation_invoice(request: web.Request) -> web.Response:
    """
    Создать invoice для поддержки проекта через Telegram Stars (НЕ для Premium).

    POST /api/miniapp/donation/create-invoice
    Body: { "telegram_id": 123, "amount": 50 }
    """
    try:
        data = await request.json()
        telegram_id = data.get("telegram_id")
        amount = data.get("amount", 50)  # Минимальная сумма 50 Stars

        if not telegram_id or amount < 50:
            return web.json_response({"error": "Invalid request data"}, status=400)

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            from aiogram import Bot

            bot = Bot(token=settings.telegram_bot_token)

            # Создаем invoice для поддержки проекта (НЕ активирует Premium)
            # Звезды отправляются на @SavinVE (админ) через provider_data
            # Для Telegram Stars нужно указать username получателя в provider_data
            import json

            provider_data = json.dumps({"username": "SavinVE"})  # Админ получает звезды

            invoice = await bot.create_invoice_link(
                title="Поддержка проекта PandaPal",
                description="Спасибо за поддержку! Это помогает развитию проекта.",
                payload=f"donation_{telegram_id}_{amount}",  # НЕ "premium_"
                currency="XTR",  # Telegram Stars currency
                prices=[{"label": "Поддержка проекта", "amount": amount}],
                provider_data=provider_data,
            )

            await bot.session.close()

            logger.info(f"✅ Stars donation invoice создан: user={telegram_id}, amount={amount}")

            return web.json_response({"success": True, "invoice_link": invoice})

    except Exception as e:
        logger.error(f"❌ Ошибка создания donation invoice: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def handle_successful_payment(request: web.Request) -> web.Response:
    """
    Обработка успешной оплаты Premium (fallback endpoint).

    POST /api/miniapp/premium/payment-success
    Body: { "telegram_id": 123, "plan_id": "month", "transaction_id": "..." }

    Примечание: Основная обработка происходит через webhook в payment_handler.py
    Этот endpoint используется как fallback или для ручной активации.
    """
    try:
        data = await request.json()

        # Валидация входных данных
        try:
            validated = PremiumPaymentRequest(**data)
        except ValidationError as e:
            logger.warning(f"⚠️ Invalid premium payment request: {e.errors()}")
            return web.json_response(
                {"error": "Invalid request data", "details": e.errors()},
                status=400,
            )

        telegram_id = validated.telegram_id
        plan_id = validated.plan_id
        transaction_id = validated.transaction_id

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Активируем подписку
            subscription_service = SubscriptionService(db)
            subscription = subscription_service.activate_subscription(
                telegram_id=telegram_id,
                plan_id=plan_id,
                transaction_id=transaction_id,
                payment_method="stars",
                payment_id=transaction_id,  # Для Stars используем transaction_id как payment_id
            )

            db.commit()

            logger.info(
                f"💰 Premium активирован через API: user={telegram_id}, "
                f"plan={plan_id}, tx={transaction_id}, expires={subscription.expires_at}"
            )

            # Отправляем уведомление пользователю
            try:
                from aiogram import Bot

                bot = Bot(token=settings.telegram_bot_token)

                # Определяем длительность для сообщения
                plan_names = {
                    "month": "месяц",
                    "year": "год",
                }
                duration = plan_names.get(plan_id, plan_id)

                await bot.send_message(
                    chat_id=telegram_id,
                    text=(
                        f"🎉 <b>Premium активирован!</b>\n\n"
                        f"✅ Подписка на {duration} успешно активирована.\n"
                        f"📅 Действует до: {subscription.expires_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                        f"Теперь у тебя есть доступ ко всем Premium функциям!"
                    ),
                    parse_mode="HTML",
                )

                # Отправляем дружелюбное сообщение от панды
                panda_messages = [
                    "Я так рад, что теперь мы будем проводить больше времени вместе! Готов помогать тебе с уроками!",
                    "Ура! Теперь у нас будет больше возможностей для учебы и игр. Давай начнем!",
                ]
                panda_message = random.choice(panda_messages)

                # Небольшая задержка перед сообщением от панды
                await asyncio.sleep(1)
                await bot.send_message(chat_id=telegram_id, text=panda_message)

                await bot.session.close()
                logger.info(f"✅ Уведомление отправлено пользователю {telegram_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки уведомления пользователю {telegram_id}: {e}")

            return web.json_response(
                {
                    "success": True,
                    "message": "Premium activated successfully",
                    "expires_at": subscription.expires_at.isoformat(),
                }
            )

    except ValueError as e:
        logger.error(f"❌ Ошибка валидации: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        # Используем % для логирования чтобы избежать проблем с фигурными скобками в SQL
        logger.error("❌ Ошибка обработки оплаты: %s", str(e), exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def create_yookassa_payment(request: web.Request) -> web.Response:
    """
    Создать платеж через ЮKassa (карта/СБП).

    POST /api/miniapp/premium/create-payment
    Body: { "telegram_id": 123, "plan_id": "month", "user_email": "user@example.com" }
    """
    try:
        data = await request.json()

        # Валидация входных данных
        try:
            validated = PremiumYooKassaRequest(**data)
        except ValidationError as e:
            logger.warning(f"⚠️ Invalid YooKassa payment request: {e.errors()}")
            return web.json_response(
                {"error": "Invalid request data", "details": e.errors()},
                status=400,
            )

        telegram_id = validated.telegram_id
        plan_id = validated.plan_id
        user_email = getattr(validated, "user_email", None)
        user_phone = getattr(validated, "user_phone", None)

        with get_db() as db:
            # Проверяем существование пользователя в БД
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                logger.warning(f"⚠️ User not found for telegram_id: {telegram_id}")
                return web.json_response({"error": "User not found"}, status=404)

            # Создаем платеж через ЮKassa
            payment_service = PaymentService()
            payment_data = await payment_service.create_payment(
                telegram_id=telegram_id,
                plan_id=plan_id,
                user_email=user_email,
                user_phone=user_phone,
            )

            # Сохраняем заказ в БД сразу после создания платежа

            from bot.models import Payment as PaymentModel

            plan = payment_service.PLANS[plan_id]
            payment_record = PaymentModel(
                payment_id=payment_data["payment_id"],
                user_telegram_id=telegram_id,
                plan_id=plan_id,
                amount=plan["price"],
                currency=payment_data["amount"]["currency"],
                status="pending",
                payment_method="yookassa_card",  # Будет уточнено при webhook
                payment_metadata={"idempotence_key": str(uuid.uuid4())},
            )
            db.add(payment_record)
            db.commit()

            logger.info(
                f"✅ ЮKassa платеж создан и сохранен: payment_id={payment_data['payment_id']}, "
                f"user={telegram_id}, plan={plan_id}"
            )

            return web.json_response(
                {
                    "success": True,
                    "payment_id": payment_data["payment_id"],
                    "confirmation_url": payment_data["confirmation_url"],
                    "amount": payment_data["amount"],
                }
            )

    except ValueError as e:
        error_msg = str(e)
        logger.error(f"❌ Ошибка валидации: {error_msg}")

        # Специальная обработка ошибки аутентификации
        if "аутентификации" in error_msg or "401" in error_msg:
            return web.json_response(
                {
                    "error": "Ошибка аутентификации ЮKassa",
                    "message": (
                        "Проверь переменные окружения в Railway: "
                        "YOOKASSA_TEST_MODE=true, YOOKASSA_TEST_SECRET_KEY=<ключ из ЛК ЮKassa>"
                    ),
                },
                status=401,
            )

        return web.json_response({"error": error_msg}, status=400)
    except Exception as e:
        error_msg = str(e)
        logger.error("❌ Ошибка создания платежа ЮKassa: %s", error_msg, exc_info=True)

        # Проверяем, не связана ли ошибка с аутентификацией
        if "401" in error_msg or "Unauthorized" in error_msg:
            return web.json_response(
                {
                    "error": "Ошибка аутентификации ЮKassa",
                    "message": (
                        "Проверь переменные окружения в Railway: "
                        "YOOKASSA_TEST_MODE=true, YOOKASSA_TEST_SECRET_KEY=<ключ из ЛК ЮKassa>"
                    ),
                },
                status=401,
            )

        return web.json_response({"error": "Internal server error"}, status=500)


async def yookassa_webhook(request: web.Request) -> web.Response:
    """
    Обработка webhook уведомлений от ЮKassa.

    POST /api/miniapp/premium/yookassa-webhook
    """
    try:
        # Получаем тело запроса для верификации подписи
        request_body = await request.text()
        signature = request.headers.get("X-Yookassa-Signature")

        # Логируем информацию о webhook для отладки
        logger.info(
            f"📥 YooKassa webhook получен: signature={'present' if signature else 'missing'}, "
            f"body_length={len(request_body)}, "
            f"ip={request.remote}"
        )

        # Верифицируем подпись webhook
        payment_service = PaymentService()
        if not payment_service.verify_webhook_signature(request_body, signature):
            logger.warning(
                "⚠️ Webhook с невалидной подписью отклонен. "
                "Проверь настройки webhook в личном кабинете YooKassa: "
                "1. URL webhook должен быть правильным "
                "2. Подпись должна быть включена "
                "3. YOOKASSA_SECRET_KEY должен совпадать с ключом в кабинете"
            )
            return web.json_response({"error": "Invalid signature"}, status=403)

        # Парсим JSON данные
        import json

        data = json.loads(request_body)

        # Логируем полную структуру webhook для отладки
        event = data.get("event", "")
        payment_object = data.get("object", {})
        payment_id = payment_object.get("id", "unknown")
        payment_status = payment_object.get("status", "unknown")
        payment_metadata = payment_object.get("metadata", {})

        logger.info(
            f"📋 Webhook событие: {event}, payment_id={payment_id}, "
            f"status={payment_status}, "
            f"metadata={payment_metadata}, "
            f"paid={payment_object.get('paid', False)}, "
            f"amount={payment_object.get('amount', {})}"
        )

        # Детальное логирование структуры webhook для отладки
        logger.debug(
            f"🔍 Полная структура webhook: {json.dumps(data, indent=2, ensure_ascii=False)}"
        )

        # Обрабатываем webhook через PaymentService
        webhook_result = payment_service.process_webhook(data)

        if not webhook_result:
            # Событие не требует обработки (например, payment.canceled, payment.waiting_for_capture)
            logger.info(f"ℹ️ Webhook событие {event} не требует активации подписки (игнорируем)")
            return web.json_response({"success": True, "message": f"Event {event} ignored"})

        payment_id = webhook_result["payment_id"]
        telegram_id = webhook_result["telegram_id"]
        plan_id = webhook_result["plan_id"]

        # Активируем подписку для авторизованных пользователей
        with get_db() as db:
            from datetime import datetime

            from sqlalchemy import select

            from bot.models import Subscription

            # Обновляем или создаем запись платежа в БД
            payment_record = db.execute(
                select(PaymentModel).where(PaymentModel.payment_id == payment_id)
            ).scalar_one_or_none()

            # Определяем способ оплаты из webhook данных
            payment_object = data.get("object", {})
            payment_method_data = payment_object.get("payment_method", {})
            payment_method_type = payment_method_data.get("type", "")

            # Логируем структуру webhook для отладки
            logger.info(
                f"📋 Webhook данные: event={data.get('event')}, "
                f"payment_id={payment_object.get('id')}, "
                f"payment_method_type={payment_method_type}, "
                f"payment_method_data={payment_method_data}"
            )

            # Маппинг типов оплаты ЮKassa на наши значения
            if payment_method_type == "bank_card":
                payment_method = "yookassa_card"
            elif payment_method_type in ("sberbank", "sbp"):
                payment_method = "yookassa_sbp"
            else:
                payment_method = "yookassa_other"

            # Сохраняем payment_method_id для автоплатежа (если есть)
            # По документации ЮKassa, если save_payment_method=True, то:
            # 1. В payment_method.saved приходит true (если карта сохранена)
            # 2. В payment_method.id приходит ID сохраненного метода оплаты
            # 3. Также может быть в payment.saved_payment_method_id
            saved_payment_method_id = None

            # Вариант 1: Проверяем payment_method.saved и payment_method.id
            if payment_method_data:
                saved = payment_method_data.get("saved", False)
                payment_method_id = payment_method_data.get("id")

                logger.info(
                    f"💳 Payment method данные: saved={saved}, "
                    f"id={payment_method_id}, type={payment_method_type}"
                )

                if saved and payment_method_id:
                    saved_payment_method_id = payment_method_id
                    logger.info(
                        f"✅ Сохраненный метод оплаты найден в payment_method: "
                        f"saved={saved}, payment_method_id={saved_payment_method_id}"
                    )

            # Вариант 2: Проверяем payment.saved_payment_method_id (альтернативный способ)
            if not saved_payment_method_id:
                saved_pm_id = payment_object.get("saved_payment_method_id")
                if saved_pm_id:
                    saved_payment_method_id = saved_pm_id
                    logger.info(
                        f"✅ Сохраненный метод оплаты найден в payment.saved_payment_method_id: "
                        f"payment_method_id={saved_payment_method_id}"
                    )

            if not saved_payment_method_id:
                logger.warning(
                    f"⚠️ Сохраненный метод оплаты не найден в webhook! "
                    f"payment_method_data={payment_method_data}, "
                    f"payment_object={payment_object.get('id')}"
                )

            # Определяем статус из события
            event = data.get("event", "")
            if event == "payment.succeeded":
                status = "succeeded"
            elif event == "payment.canceled":
                status = "cancelled"
            elif event == "payment.waiting_for_capture":
                status = "pending"  # Платеж ожидает подтверждения
                logger.info(f"⏳ Платеж {payment_id} ожидает подтверждения (capture)")
            elif event == "payment.failed":
                status = "failed"
            elif event == "refund.succeeded":
                status = "refunded"  # Возврат успешен
                logger.info(f"💰 Возврат успешен для платежа {payment_id}")
            else:
                status = "pending"
                logger.info(f"ℹ️ Неизвестное событие: {event}, статус={status}")

            if payment_record:
                # Обновляем существующую запись
                payment_record.status = status
                payment_record.payment_method = payment_method
                payment_record.webhook_data = data
                if status == "succeeded":
                    payment_record.paid_at = datetime.now(UTC)
            else:
                # Создаем новую запись если не была создана при создании платежа
                amount_value = payment_object.get("amount", {}).get("value", "0")
                payment_record = PaymentModel(
                    payment_id=payment_id,
                    user_telegram_id=telegram_id,
                    plan_id=plan_id,
                    amount=float(amount_value),
                    currency=payment_object.get("amount", {}).get("currency", "RUB"),
                    status=status,
                    payment_method=payment_method,
                    webhook_data=data,
                    paid_at=datetime.now(UTC) if status == "succeeded" else None,
                )
                db.add(payment_record)

            db.commit()

            # Проверяем, не активирована ли уже подписка для этого платежа
            subscription_service = SubscriptionService(db)

            existing = db.execute(
                select(Subscription).where(Subscription.payment_id == payment_id)
            ).scalar_one_or_none()

            if existing:
                logger.warning(f"⚠️ Подписка уже активирована для платежа {payment_id}")
                return web.json_response(
                    {"success": True, "message": "Subscription already activated"}
                )

            # Активируем подписку только для успешных платежей
            if status == "succeeded":
                # Дополнительная проверка статуса через API (fallback)
                payment_status = await payment_service.get_payment_status(payment_id)
                if payment_status and payment_status["status"] != "succeeded":
                    logger.warning(
                        f"⚠️ Статус платежа {payment_id} не совпадает: "
                        f"webhook={status}, api={payment_status['status']}"
                    )

                logger.info(
                    f"💰 Активируем подписку: user={telegram_id}, plan={plan_id}, "
                    f"payment_id={payment_id}, saved_payment_method_id={saved_payment_method_id}"
                )

                subscription = subscription_service.activate_subscription(
                    telegram_id=telegram_id,
                    plan_id=plan_id,
                    payment_method=payment_method,
                    payment_id=payment_id,
                    saved_payment_method_id=saved_payment_method_id,
                )

                logger.info(
                    f"✅ Подписка активирована: subscription_id={subscription.id}, "
                    f"saved_payment_method_id={subscription.saved_payment_method_id}, "
                    f"auto_renew={subscription.auto_renew}"
                )

                # Связываем подписку с платежом
                payment_record.subscription_id = subscription.id
                db.commit()

                logger.info(
                    f"💰 Premium активирован через ЮKassa webhook: user={telegram_id}, "
                    f"plan={plan_id}, payment_id={payment_id}, expires={subscription.expires_at}"
                )

                # Отправляем уведомление пользователю
                try:
                    from aiogram import Bot

                    bot = Bot(token=settings.telegram_bot_token)

                    # Определяем длительность для сообщения
                    plan_names = {
                        "month": "месяц",
                        "year": "год",
                    }
                    duration = plan_names.get(plan_id, plan_id)

                    await bot.send_message(
                        chat_id=telegram_id,
                        text=(
                            f"🎉 <b>Premium активирован!</b>\n\n"
                            f"✅ Подписка на {duration} успешно активирована.\n"
                            f"📅 Действует до: {subscription.expires_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                            f"Теперь у тебя есть доступ ко всем Premium функциям!"
                        ),
                        parse_mode="HTML",
                    )

                    # Отправляем дружелюбное сообщение от панды
                    panda_messages = [
                        "🐼 Я так рада, что теперь мы будем проводить больше времени вместе! Готов помогать тебе с уроками!",
                        "🐼 Ура! Теперь у нас будет больше возможностей для учебы и игр. Давай начнем!",
                    ]
                    panda_message = random.choice(panda_messages)

                    # Небольшая задержка перед сообщением от панды
                    await asyncio.sleep(1)
                    await bot.send_message(chat_id=telegram_id, text=panda_message)

                    await bot.session.close()
                    logger.info(f"✅ Уведомление отправлено пользователю {telegram_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки уведомления пользователю {telegram_id}: {e}")

                return web.json_response({"success": True, "message": "Subscription activated"})
            else:
                logger.info(
                    f"ℹ️ Webhook получен для платежа {payment_id} со статусом {status}, "
                    "подписка не активирована"
                )
                return web.json_response(
                    {"success": True, "message": f"Payment status updated to {status}"}
                )

    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка парсинга JSON в webhook: {e}")
        return web.json_response({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error("❌ Ошибка обработки webhook ЮKassa: %s", str(e), exc_info=True)
        # Всегда возвращаем 200, чтобы ЮKassa не повторял запрос
        return web.json_response({"success": False, "error": str(e)}, status=200)


async def get_premium_status(request: web.Request) -> web.Response:
    """
    Получить статус Premium подписки пользователя.

    GET /api/miniapp/premium/status/{telegram_id}
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])

        with get_db() as db:
            subscription_service = SubscriptionService(db)
            is_premium = subscription_service.is_premium_active(telegram_id)
            active_subscription = subscription_service.get_active_subscription(telegram_id)

            # Детальное логирование для отладки
            logger.info(
                f"🔍 Premium статус для user={telegram_id}: "
                f"is_premium={is_premium}, "
                f"has_active_subscription={active_subscription is not None}, "
                f"saved_payment_method_id={active_subscription.saved_payment_method_id if active_subscription else None}, "
                f"has_saved_payment_method={bool(active_subscription.saved_payment_method_id) if active_subscription else False}"
            )

            status_data = {
                "is_premium": is_premium,
                "active_subscription": (
                    active_subscription.to_dict() if active_subscription else None
                ),
            }

            return web.json_response({"success": True, **status_data})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid telegram_id: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса Premium: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def remove_saved_payment_method(request: web.Request) -> web.Response:
    """
    Удалить сохраненный способ оплаты (отвязать карту).

    POST /api/miniapp/premium/remove-payment-method
    Body: { "telegram_id": 123 }

    Отвязывает сохраненную карту - удаляет saved_payment_method_id из БД
    и отключает автоплатежи. В ЮKassa нельзя удалить способ оплаты через API,
    но удаление из нашей БД отключает автоплатежи.
    """
    try:
        data = await request.json()
        telegram_id = data.get("telegram_id")

        if not telegram_id:
            return web.json_response({"error": "telegram_id is required"}, status=400)

        telegram_id = validate_telegram_id(telegram_id)

        with get_db() as db:
            subscription_service = SubscriptionService(db)
            removed = subscription_service.remove_saved_payment_method(telegram_id)

            if not removed:
                return web.json_response(
                    {"success": False, "message": "No saved payment method found"},
                    status=404,
                )

            db.commit()

            logger.info(f"✅ Способ оплаты отвязан: user={telegram_id}")

            return web.json_response(
                {
                    "success": True,
                    "message": "Payment method removed successfully",
                }
            )

    except ValueError as e:
        logger.warning(f"⚠️ Invalid telegram_id: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка отвязки способа оплаты: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


def setup_premium_routes(app: web.Application) -> None:
    """Регистрация роутов Premium (только ЮKassa)"""
    app.router.add_post("/api/miniapp/premium/create-payment", create_yookassa_payment)
    app.router.add_post("/api/miniapp/premium/payment-success", handle_successful_payment)
    app.router.add_post("/api/miniapp/premium/yookassa-webhook", yookassa_webhook)
    app.router.add_get("/api/miniapp/premium/status/{telegram_id}", get_premium_status)
    app.router.add_post("/api/miniapp/premium/remove-payment-method", remove_saved_payment_method)
    # Donation endpoint (для поддержки проекта через Stars)
    app.router.add_post("/api/miniapp/donation/create-invoice", create_donation_invoice)

    logger.info("💰 Premium API routes зарегистрированы (только ЮKassa)")
