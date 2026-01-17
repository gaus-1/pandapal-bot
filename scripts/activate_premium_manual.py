#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для ручной активации Premium подписки пользователю.

Использовать когда webhook не сработал или нужно активировать вручную.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Настройка кодировки для Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Добавляем корневую папку в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from bot.database import get_db
from bot.models import Subscription


def activate_premium(telegram_id: int, plan: str = "month", payment_id: str = None):
    """
    Активирует Premium подписку для пользователя.

    Args:
        telegram_id: ID пользователя в Telegram
        plan: Тип подписки (month, year)
        payment_id: ID платежа YooKassa (опционально)
    """

    # Определяем длительность подписки
    duration_map = {"month": 30, "year": 365}

    if plan not in duration_map:
        print(f"❌ Неизвестный план: {plan}")
        print(f"   Доступные: {', '.join(duration_map.keys())}")
        sys.exit(1)

    duration_days = duration_map[plan]

    # Создаём подписку
    with get_db() as db:
        # Проверяем существующие активные подписки
        existing = (
            db.query(Subscription)
            .filter(Subscription.user_telegram_id == telegram_id, Subscription.is_active == True)
            .first()
        )

        if existing:
            print(f"⚠️ У пользователя {telegram_id} уже есть активная подписка")
            print(f"   Истекает: {existing.expires_at}")
            response = input("   Продлить подписку? (y/n): ")
            if response.lower() != "y":
                print("❌ Отменено")
                sys.exit(0)

            # Деактивируем старую подписку
            existing.is_active = False
            db.commit()
            print(f"✅ Старая подписка деактивирована")

        # Создаём новую подписку
        now = datetime.utcnow()
        expires_at = now + timedelta(days=duration_days)

        subscription = Subscription(
            user_telegram_id=telegram_id,
            plan_id=plan,
            starts_at=now,
            expires_at=expires_at,
            is_active=True,
            transaction_id=payment_id or f"manual_{telegram_id}_{int(now.timestamp())}",
            payment_method="yookassa_sbp",  # СБП оплата
            payment_id=payment_id,
        )

        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        print(f"\n✅ Premium подписка активирована!")
        print(f"   Пользователь: {telegram_id}")
        print(f"   План: {plan}")
        print(f"   Начало: {subscription.starts_at}")
        print(f"   Окончание: {subscription.expires_at}")
        print(f"   ID подписки: {subscription.id}")

        if payment_id:
            print(f"   Платёж YooKassa: {payment_id}")


if __name__ == "__main__":
    # Для Вячеслава
    telegram_id = 963126718
    plan = "month"
    payment_id = "30ecc421-000f-5001-8000-1fbb0ea447b2"

    print(f"🚀 Активация Premium для пользователя {telegram_id}")
    print(f"   План: {plan} (30 дней)")
    print(f"   Платёж: {payment_id}")
    print()

    activate_premium(telegram_id, plan, payment_id)
