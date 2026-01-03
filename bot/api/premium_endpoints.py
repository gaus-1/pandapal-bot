"""
Premium endpoints - Обработка платежей через Telegram Stars и ЮKassa
"""

from aiohttp import web
from loguru import logger
from pydantic import ValidationError

from bot.api.validators import (
    PremiumInvoiceRequest,
    PremiumPaymentRequest,
    PremiumYooKassaRequest,
    validate_telegram_id,
)
from bot.config import settings
from bot.database import get_db
from bot.services import PaymentService, SubscriptionService, UserService


async def create_premium_invoice(request: web.Request) -> web.Response:
    """
    Создать invoice для оплаты Premium через Telegram Stars.

    POST /api/miniapp/premium/create-invoice
    Body: { "telegram_id": 123, "plan_id": "month", "payment_method": "stars" }
    """
    try:
        data = await request.json()

        # Валидация входных данных
        try:
            validated = PremiumInvoiceRequest(**data)
        except ValidationError as e:
            logger.warning(f"⚠️ Invalid premium invoice request: {e.errors()}")
            return web.json_response(
                {"error": "Invalid request data", "details": e.errors()},
                status=400,
            )

        telegram_id = validated.telegram_id
        plan_id = validated.plan_id
        payment_method = getattr(validated, "payment_method", "stars")

        # Тарифные планы для Telegram Stars (старые цены)
        stars_plans = {
            "week": {"name": "Premium на неделю", "price": 50, "days": 7},
            "month": {"name": "Premium на месяц", "price": 150, "days": 30},
            "year": {"name": "Premium на год", "price": 999, "days": 365},
        }

        plan = stars_plans.get(plan_id)
        if not plan:
            return web.json_response({"error": "Invalid plan_id"}, status=400)

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Создаем invoice через Telegram Bot API (только для Stars)
            if payment_method == "stars":
                from aiogram import Bot

                bot = Bot(token=settings.telegram_bot_token)

                # Создаем invoice с Telegram Stars
                invoice = await bot.create_invoice_link(
                    title=plan["name"],
                    description=f"PandaPal Premium доступ на {plan['days']} дней",
                    payload=f"premium_{plan_id}_{telegram_id}",
                    currency="XTR",  # Telegram Stars currency
                    prices=[{"label": plan["name"], "amount": plan["price"]}],
                )

                await bot.session.close()

                logger.info(f"✅ Stars invoice создан для пользователя {telegram_id}: {plan_id}")

                return web.json_response({"success": True, "invoice_link": invoice})
            else:
                return web.json_response(
                    {"error": "Use /api/miniapp/premium/create-payment for card/SBP payments"},
                    status=400,
                )

    except Exception as e:
        logger.error(f"❌ Ошибка создания invoice: {e}")
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
            )

            db.commit()

            logger.info(
                f"💰 Premium активирован через API: user={telegram_id}, "
                f"plan={plan_id}, tx={transaction_id}, expires={subscription.expires_at}"
            )

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
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Создаем платеж через ЮKassa
            payment_service = PaymentService()
            payment_data = payment_service.create_payment(
                telegram_id=telegram_id,
                plan_id=plan_id,
                user_email=user_email,
                user_phone=user_phone,
            )

            logger.info(
                f"✅ ЮKassa платеж создан: payment_id={payment_data['payment_id']}, "
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
        logger.error(f"❌ Ошибка валидации: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error("❌ Ошибка создания платежа ЮKassa: %s", str(e), exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def yookassa_webhook(request: web.Request) -> web.Response:
    """
    Обработка webhook уведомлений от ЮKassa.

    POST /api/miniapp/premium/yookassa-webhook
    """
    try:
        data = await request.json()

        # Обрабатываем webhook через PaymentService
        payment_service = PaymentService()
        webhook_result = payment_service.process_webhook(data)

        if not webhook_result:
            # Событие не требует обработки
            return web.json_response({"success": True, "message": "Event ignored"})

        payment_id = webhook_result["payment_id"]
        telegram_id = webhook_result["telegram_id"]
        plan_id = webhook_result["plan_id"]

        # Активируем подписку
        with get_db() as db:
            subscription_service = SubscriptionService(db)

            # Проверяем, не активирована ли уже подписка для этого платежа
            from bot.models import Subscription
            from sqlalchemy import select

            existing = db.execute(
                select(Subscription).where(Subscription.payment_id == payment_id)
            ).scalar_one_or_none()

            if existing:
                logger.warning(
                    f"⚠️ Подписка уже активирована для платежа {payment_id}"
                )
                return web.json_response(
                    {"success": True, "message": "Subscription already activated"}
                )

            # Определяем способ оплаты из платежа
            payment_status = payment_service.get_payment_status(payment_id)
            payment_method = "yookassa_other"
            if payment_status:
                # Можно определить по payment_method в ответе, но для простоты используем общий
                payment_method = "yookassa_card"  # По умолчанию карта

            subscription = subscription_service.activate_subscription(
                telegram_id=telegram_id,
                plan_id=plan_id,
                payment_method=payment_method,
                payment_id=payment_id,
            )

            db.commit()

            logger.info(
                f"💰 Premium активирован через ЮKassa webhook: user={telegram_id}, "
                f"plan={plan_id}, payment_id={payment_id}, expires={subscription.expires_at}"
            )

            return web.json_response({"success": True, "message": "Subscription activated"})

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

            status_data = {
                "is_premium": is_premium,
                "active_subscription": active_subscription.to_dict() if active_subscription else None,
            }

            return web.json_response({"success": True, **status_data})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid telegram_id: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса Premium: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


def setup_premium_routes(app: web.Application) -> None:
    """Регистрация роутов Premium"""
    app.router.add_post("/api/miniapp/premium/create-invoice", create_premium_invoice)
    app.router.add_post("/api/miniapp/premium/create-payment", create_yookassa_payment)
    app.router.add_post("/api/miniapp/premium/payment-success", handle_successful_payment)
    app.router.add_post("/api/miniapp/premium/yookassa-webhook", yookassa_webhook)
    app.router.add_get("/api/miniapp/premium/status/{telegram_id}", get_premium_status)

    logger.info("💰 Premium API routes зарегистрированы")
