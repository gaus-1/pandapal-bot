"""
Конфигурация для тестов платежей
Устанавливает переменные окружения перед импортом модулей
"""

import os

import pytest

# Устанавливаем переменные окружения ДО импорта bot модулей
os.environ.setdefault("DATABASE_URL", "sqlite:///test_payment.db")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token_12345")
os.environ.setdefault("YANDEX_CLOUD_API_KEY", "test_api_key")
os.environ.setdefault("YANDEX_CLOUD_FOLDER_ID", "test_folder_id")
os.environ.setdefault("SECRET_KEY", "test_secret_key_32_chars_long_12345")
os.environ.setdefault("YOOKASSA_SHOP_ID", "test_shop_id")
os.environ.setdefault("YOOKASSA_SECRET_KEY", "test_secret_key")
os.environ.setdefault("YOOKASSA_RETURN_URL", "https://test.example.com/return")
os.environ.setdefault("YOOKASSA_INN", "123456789012")
