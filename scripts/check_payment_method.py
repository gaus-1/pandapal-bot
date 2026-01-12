"""
Скрипт для проверки сохранённого способа оплаты в платеже ЮKassa.

Использование:
    python scripts/check_payment_method.py <payment_id>

Пример:
    python scripts/check_payment_method.py 30f6d4ed-000f-5001-8000-155de97f23de
"""

import asyncio
import json
import sys

from loguru import logger
from yookassa import Configuration, Payment

from bot.config import settings
from bot.services.payment_service import PaymentService


async def check_payment_method(payment_id: str) -> None:
    """Проверить сохранённый способ оплаты в платеже."""
    # Настраиваем ЮKassa
    Configuration.account_id = settings.active_yookassa_shop_id
    Configuration.secret_key = settings.active_yookassa_secret_key

    logger.info(f"🔍 Проверка платежа: {payment_id}")
    logger.info(f"💳 Режим: {'ТЕСТОВЫЙ' if settings.yookassa_test_mode else 'ПРОДАКШН'}")
    logger.info(f"🏪 Shop ID: {settings.active_yookassa_shop_id}")

    try:
        # Получаем полный объект платежа через API
        payment = await asyncio.to_thread(Payment.find_one, payment_id)

        logger.info(f"✅ Платеж найден: status={payment.status}, paid={payment.paid}")

        # Проверяем payment_method
        if hasattr(payment, "payment_method") and payment.payment_method:
            pm = payment.payment_method
            logger.info("=" * 80)
            logger.info("💳 PAYMENT_METHOD:")
            logger.info(f"   type: {pm.type if hasattr(pm, 'type') else 'N/A'}")
            logger.info(f"   id: {pm.id if hasattr(pm, 'id') else 'N/A'}")
            logger.info(f"   saved: {pm.saved if hasattr(pm, 'saved') else 'N/A'}")
            if hasattr(pm, "card") and pm.card:
                card = pm.card
                logger.info(f"   card.last4: {card.last4 if hasattr(card, 'last4') else 'N/A'}")
                logger.info(f"   card.first6: {card.first6 if hasattr(card, 'first6') else 'N/A'}")
            logger.info("=" * 80)

            # Выводим полный JSON для копирования
            payment_dict = {
                "id": payment.id,
                "status": payment.status,
                "paid": payment.paid,
                "payment_method": {
                    "type": pm.type if hasattr(pm, "type") else None,
                    "id": pm.id if hasattr(pm, "id") else None,
                    "saved": pm.saved if hasattr(pm, "saved") else None,
                },
            }

            # Добавляем card данные если есть
            if hasattr(pm, "card") and pm.card:
                card = pm.card
                payment_dict["payment_method"]["card"] = {
                    "last4": card.last4 if hasattr(card, "last4") else None,
                    "first6": card.first6 if hasattr(card, "first6") else None,
                }

            logger.info("\n📋 JSON для копирования:")
            logger.info(json.dumps(payment_dict, indent=2, ensure_ascii=False))

            # Проверяем наличие saved_payment_method_id на корне объекта
            if hasattr(payment, "saved_payment_method_id") and payment.saved_payment_method_id:
                logger.info(
                    f"\n✅ saved_payment_method_id (на корне): {payment.saved_payment_method_id}"
                )

            # Итоговый вывод
            if hasattr(pm, "saved") and pm.saved and hasattr(pm, "id") and pm.id:
                logger.info("\n✅ КАРТА СОХРАНЕНА ДЛЯ АВТОПЛАТЕЖЕЙ!")
                logger.info(f"   payment_method.id = {pm.id}")
            else:
                logger.warning("\n⚠️ КАРТА НЕ СОХРАНЕНА!")
                if not (hasattr(pm, "saved") and pm.saved):
                    logger.warning("   payment_method.saved != true")
                if not (hasattr(pm, "id") and pm.id):
                    logger.warning("   payment_method.id отсутствует")

        else:
            logger.warning("⚠️ payment_method отсутствует в объекте платежа")

        # Выводим полный объект платежа (для отладки)
        logger.info("\n📦 Полный объект платежа (первые 2000 символов):")
        try:
            payment_json = json.dumps(payment.__dict__, indent=2, ensure_ascii=False, default=str)
            logger.info(payment_json[:2000])
            if len(payment_json) > 2000:
                logger.info(f"... (ещё {len(payment_json) - 2000} символов)")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось сериализовать объект: {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка получения платежа: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python scripts/check_payment_method.py <payment_id>")
        print("Пример: python scripts/check_payment_method.py 30f6d4ed-000f-5001-8000-155de97f23de")
        sys.exit(1)

    payment_id = sys.argv[1]
    asyncio.run(check_payment_method(payment_id))
