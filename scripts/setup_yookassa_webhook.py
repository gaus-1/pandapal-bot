#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для настройки webhook в YooKassa через API.

Настраивает HTTP-уведомления для получения информации о статусе платежей.
"""

import os
import sys
from pathlib import Path

# Добавляем корневую папку в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from yookassa import Configuration, Webhook


def setup_webhook():
    """Настройка webhook для YooKassa."""

    # Получаем данные из переменных окружения
    shop_id = os.getenv("YOOKASSA_SHOP_ID")
    secret_key = os.getenv("YOOKASSA_SECRET_KEY")
    webhook_domain = os.getenv("WEBHOOK_DOMAIN", "web-production-725aa.up.railway.app")

    if not shop_id or not secret_key:
        print("❌ Ошибка: YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY должны быть установлены")
        print("Экспортируй переменные:")
        print("  export YOOKASSA_SHOP_ID=1240345")
        print("  export YOOKASSA_SECRET_KEY=live_...")
        sys.exit(1)

    # Настраиваем YooKassa SDK
    Configuration.account_id = shop_id
    Configuration.secret_key = secret_key

    print(f"🔧 Настройка webhook для магазина {shop_id}")
    print(f"🌐 Домен: {webhook_domain}")

    # URL для webhook
    webhook_url = f"https://{webhook_domain}/api/miniapp/premium/yookassa-webhook"

    try:
        # Получаем список существующих webhook
        print("\n📋 Проверка существующих webhook...")
        webhooks = Webhook.list()

        # Удаляем старые webhook для этого URL (если есть)
        for webhook in webhooks.items:
            if webhook.url == webhook_url:
                print(f"🗑️ Удаление старого webhook: {webhook.id}")
                Webhook.remove(webhook.id)

        # Создаём новый webhook
        print(f"\n➕ Создание нового webhook: {webhook_url}")
        webhook = Webhook.add({"event": "payment.succeeded", "url": webhook_url})

        print(f"✅ Webhook успешно создан!")
        print(f"   ID: {webhook.id}")
        print(f"   URL: {webhook.url}")
        print(f"   Event: {webhook.event}")

        # Создаём webhook для отмены платежа (опционально)
        print(f"\n➕ Создание webhook для отмены платежей...")
        webhook_canceled = Webhook.add({"event": "payment.canceled", "url": webhook_url})

        print(f"✅ Webhook для отмены создан!")
        print(f"   ID: {webhook_canceled.id}")
        print(f"   Event: {webhook_canceled.event}")

        # Показываем все активные webhook
        print("\n📋 Все активные webhook:")
        webhooks = Webhook.list()
        for wh in webhooks.items:
            print(f"   • {wh.event}: {wh.url}")

        print("\n✅ Настройка webhook завершена успешно!")

    except Exception as e:
        print(f"\n❌ Ошибка при настройке webhook: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_webhook()
