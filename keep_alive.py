#!/usr/bin/env python3
"""
Keep Alive сервис для предотвращения сна Render на FREE плане.

Периодически отправляет HTTP запросы к сервису для поддержания активности.
"""

import asyncio
import logging
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)


async def keep_alive_ping():
    """
    Отправляет ping запрос к сервису для поддержания активности.
    """
    try:
        async with aiohttp.ClientSession() as session:
            # Ping к health endpoint
            async with session.get("http://localhost:10000/health") as response:
                if response.status == 200:
                    logger.info("✅ Keep Alive ping успешен")
                else:
                    logger.warning(f"⚠️ Keep Alive ping неуспешен: {response.status}")
    except Exception as e:
        logger.error(f"❌ Ошибка Keep Alive ping: {e}")


async def keep_alive_loop():
    """
    Основной цикл Keep Alive с интервалом 10 минут.
    """
    logger.info("🔄 Keep Alive сервис запущен (интервал: 10 минут)")

    while True:
        try:
            await keep_alive_ping()
            await asyncio.sleep(600)  # 10 минут
        except Exception as e:
            logger.error(f"❌ Ошибка в Keep Alive цикле: {e}")
            await asyncio.sleep(60)  # При ошибке ждём 1 минуту


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(keep_alive_loop())
