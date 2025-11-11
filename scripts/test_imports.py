#!/usr/bin/env python3
"""
Тест импортов для проверки совместимости
"""

import sys

print(f"Python версия: {sys.version}")

try:
    print("Тестируем основные импорты...")

    # Основные библиотеки
    import asyncio

    print("OK asyncio")

    import aiohttp

    print("OK aiohttp")

    from aiogram import Bot, Dispatcher

    print("OK aiogram")

    from loguru import logger

    print("OK loguru")

    # Наши модули
    from bot.config import settings

    print("OK bot.config")

    from bot.database import init_db

    print("OK bot.database")

    from bot.handlers import routers

    print("OK bot.handlers")

    from bot.monitoring import monitoring_service

    print("OK bot.monitoring")

    print("\nВсе импорты успешны!")

except Exception as e:
    print(f"Ошибка импорта: {e}")
    sys.exit(1)
