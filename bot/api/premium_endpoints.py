"""
Premium endpoints - Обработка платежей через Telegram Stars
"""

from aiohttp import web
from loguru import logger

from bot.config import settings
from bot.database import get_db
from bot.services import SubscriptionService, UserService


async def create_premium_invoice(request: web.Request) -> web.Response:
    """
    Создать invoice для оплаты Premium через Telegram Stars.

    POST /api/miniapp/premium/create-invoice
    Body: { "telegram_id": 123, "plan_id": "month" }
    """
    try:
        data = await request.json()
        telegram_id = data.get("telegram_id")
        plan_id = data.get("plan_id")

        if not telegram_id or not plan_id:
            return web.json_response({"error": "telegram_id and plan_id required"}, status=400)

        # Тарифные планы
        plans = {
            "week": {"name": "Premium на неделю", "price": 50, "days": 7},
            "month": {"name": "Premium на месяц", "price": 150, "days": 30},
            "year": {"name": "Premium на год", "price": 999, "days": 365},
        }

        plan = plans.get(plan_id)
        if not plan:
            return web.json_response({"error": "Invalid plan_id"}, status=400)

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Создаем invoice через Telegram Bot API
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

            logger.info(f"✅ Invoice создан для пользователя {telegram_id}: {plan_id}")

            return web.json_response({"success": True, "invoice_link": invoice})

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
        telegram_id = data.get("telegram_id")
        plan_id = data.get("plan_id")
        transaction_id = data.get("transaction_id")

        if not telegram_id or not plan_id:
            return web.json_response({"error": "telegram_id and plan_id required"}, status=400)

        # Валидация plan_id
        valid_plans = ["week", "month", "year"]
        if plan_id not in valid_plans:
            return web.json_response({"error": "Invalid plan_id"}, status=400)

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
        logger.error(f"❌ Ошибка обработки оплаты: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


def setup_premium_routes(app: web.Application) -> None:
    """Регистрация роутов Premium"""
    app.router.add_post("/api/miniapp/premium/create-invoice", create_premium_invoice)
    app.router.add_post("/api/miniapp/premium/payment-success", handle_successful_payment)

    logger.info("💰 Premium API routes зарегистрированы")
