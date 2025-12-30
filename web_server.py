#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Веб-сервер для запуска PandaPal Telegram бота через webhook.

Этот модуль инициализирует aiogram Bot и Dispatcher, настраивает webhook
для работы на Render.com и запускает aiohttp сервер для приема обновлений
от Telegram.

Основные компоненты:
- Инициализация Bot и Dispatcher
- Регистрация всех обработчиков из bot/handlers
- Настройка webhook для Render.com
- HTTP сервер для приема webhook запросов
- Health check endpoints
- Интеграция метрик

Архитектура:
- SOLID принципы: разделение ответственности между инициализацией и запуском
- ООП: использование классов для организации кода
- PEP8: соблюдение стандартов кодирования
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем корневую папку в PYTHONPATH ПЕРЕД импортами
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.enums import ParseMode  # noqa: E402
from aiogram.fsm.storage.memory import MemoryStorage  # noqa: E402
from aiogram.webhook.aiohttp_server import setup_application  # noqa: E402
from aiohttp import web  # noqa: E402
from loguru import logger  # noqa: E402

from bot.config import settings  # noqa: E402
from bot.database import init_database  # noqa: E402
from bot.handlers import routers  # noqa: E402

# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level,
)


class PandaPalBotServer:
    """
    Сервер для запуска PandaPal Telegram бота.

    Реализует принцип единственной ответственности (SRP) -
    отвечает только за инициализацию и запуск бота через webhook.
    """

    def __init__(self):
        """Инициализация сервера бота."""
        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None
        self.app: web.Application | None = None
        self.settings = settings

    async def init_bot(self) -> None:
        """
        Инициализация Bot и Dispatcher.

        Создает экземпляры Bot и Dispatcher, настраивает storage
        и регистрирует все обработчики из bot/handlers.
        """
        try:
            logger.info("🤖 Инициализация Telegram бота...")

            # Создаем Bot с настройками по умолчанию
            self.bot = Bot(
                token=self.settings.telegram_bot_token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )

            # Создаем Dispatcher с MemoryStorage
            storage = MemoryStorage()
            self.dp = Dispatcher(storage=storage)

            # Регистрируем все роутеры
            for router in routers:
                self.dp.include_router(router)
                logger.debug(f"✅ Зарегистрирован роутер: {router.name}")

            logger.info(f"✅ Зарегистрировано роутеров: {len(routers)}")
            logger.info("✅ Bot и Dispatcher инициализированы")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации бота: {e}")
            raise

    async def setup_webhook(self) -> str:
        """
        Настройка webhook для Telegram.

        Устанавливает webhook URL на указанный домен.
        Автоматически определяет протокол (https) и порт.

        Returns:
            str: URL webhook для логирования
        """
        try:
            webhook_url = f"https://{self.settings.webhook_domain}/webhook"
            logger.info(f"🔗 Установка webhook: {webhook_url}")

            # Устанавливаем webhook
            await self.bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,  # Удаляем старые обновления
            )

            # Проверяем, что webhook установлен
            webhook_info = await self.bot.get_webhook_info()
            logger.info(f"✅ Webhook установлен: {webhook_info.url}")
            logger.info(f"📊 Webhook info: {webhook_info}")

            return webhook_url

        except Exception as e:
            logger.error(f"❌ Ошибка установки webhook: {e}")
            raise

    def create_app(self) -> web.Application:
        """
        Создание aiohttp приложения.

        Создает веб-приложение с маршрутами для webhook,
        health check и метрик.

        Returns:
            web.Application: Настроенное веб-приложение
        """
        try:
            logger.info("🌐 Создание веб-приложения...")

            # Создаем приложение
            self.app = web.Application()

            # Health check endpoints
            async def health_check(request: web.Request) -> web.Response:
                """Health check endpoint."""
                bot_info = None
                if self.bot:
                    try:
                        bot_info = await self.bot.get_me()
                    except Exception as bot_error:
                        logger.warning("⚠️ Не удалось получить информацию о боте: %s", bot_error)

                return web.json_response(
                    {
                        "status": "ok",
                        "mode": "webhook",
                        "webhook_url": f"https://{self.settings.webhook_domain}/webhook",
                        "bot_username": bot_info.username if bot_info else None,
                    }
                )

            async def root_handler(request: web.Request) -> web.Response:
                """Root endpoint - редирект на health check."""
                return await health_check(request)

            # Регистрируем маршруты ДО setup_application
            self.app.router.add_get("/health", health_check)
            self.app.router.add_get("/", root_handler)

            # Интегрируем метрики (если доступны)
            try:
                from bot.api.metrics_endpoint import add_metrics_to_web_server

                add_metrics_to_web_server(self.app)
                logger.info("📊 Метрики интегрированы в веб-сервер")
            except ImportError:
                logger.debug("📊 Метрики недоступны (опционально)")

            # Настраиваем webhook handler ПОСЛЕ регистрации всех маршрутов
            # Используем setup_application для правильной интеграции aiogram с aiohttp
            setup_application(self.app, self.dp, bot=self.bot)

            logger.info("✅ Веб-приложение создано")
            return self.app

        except Exception as e:
            logger.error(f"❌ Ошибка создания приложения: {e}")
            raise

    async def startup(self) -> None:
        """Запуск сервера - инициализация всех компонентов."""
        try:
            logger.info("🚀 Запуск PandaPal Bot Server...")

            # Инициализация базы данных
            await init_database()
            logger.info("📊 База данных инициализирована")

            # Инициализация бота
            await self.init_bot()

            # Настройка webhook
            webhook_url = await self.setup_webhook()

            # Создание веб-приложения
            self.create_app()

            logger.info("✅ Сервер готов к работе")
            logger.info(f"🌐 Webhook URL: {webhook_url}")
            logger.info(f"🏥 Health check: https://{self.settings.webhook_domain}/health")

        except Exception as e:
            logger.error(f"❌ Ошибка запуска сервера: {e}")
            raise

    async def shutdown(self) -> None:
        """Остановка сервера - очистка ресурсов."""
        try:
            logger.info("🛑 Остановка сервера...")

            # Удаляем webhook (опционально, для чистоты)
            if self.bot:
                try:
                    await self.bot.delete_webhook(drop_pending_updates=False)
                    logger.info("✅ Webhook удален")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка удаления webhook: {e}")

            # Закрываем сессию бота
            if self.bot:
                await self.bot.session.close()
                logger.info("✅ Сессия бота закрыта")

            logger.info("✅ Сервер остановлен")

        except Exception as e:
            logger.error(f"❌ Ошибка остановки сервера: {e}")

    async def run(self) -> None:
        """
        Запуск веб-сервера.

        Определяет порт из переменных окружения или использует 10000 по умолчанию.
        Запускает aiohttp сервер для приема webhook запросов.
        """
        try:
            # Получаем порт и хост из переменных окружения
            # Railway/Render требуют 0.0.0.0 для публичного доступа
            port = int(os.getenv("PORT", "10000"))
            host = os.getenv("HOST", "0.0.0.0")

            logger.info(f"🌐 Запуск веб-сервера на {host}:{port}")

            # Запускаем веб-сервер
            runner = web.AppRunner(self.app)
            await runner.setup()

            site = web.TCPSite(runner, host, port)
            await site.start()

            logger.info(f"✅ Сервер запущен на порту {port}")
            logger.info("📡 Ожидание обновлений от Telegram...")

            # Ждем бесконечно (сервер работает)
            await asyncio.Event().wait()

        except Exception as e:
            logger.error(f"❌ Ошибка запуска веб-сервера: {e}")
            raise
        finally:
            await self.shutdown()


async def main() -> None:
    """
    Главная функция запуска сервера.

    Создает экземпляр PandaPalBotServer и запускает его.
    """
    server = PandaPalBotServer()

    try:
        # Запуск сервера
        await server.startup()
        await server.run()

    except KeyboardInterrupt:
        logger.info("⚠️ Получен сигнал прерывания (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        await server.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Завершение работы сервера")
        sys.exit(0)
