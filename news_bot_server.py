#!/usr/bin/env python3
"""
Веб-сервер для запуска новостного бота через webhook.

Отдельный entry point для новостного бота @News_Panda_bot.
Использует ту же БД и сервисы, но отдельный бот и handlers.
"""

import asyncio
import contextlib
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
from aiogram.fsm.storage.redis import RedisStorage  # noqa: E402
from aiogram.webhook.aiohttp_server import SimpleRequestHandler  # noqa: E402
from aiohttp import web  # noqa: E402
from loguru import logger  # noqa: E402
from redis.asyncio import Redis  # noqa: E402

from bot.config.news_bot_settings import news_bot_settings  # noqa: E402
from bot.database import init_database  # noqa: E402
from bot.handlers.news_bot import router as news_bot_router  # noqa: E402

# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO",
)


class NewsBotServer:
    """Сервер для запуска новостного бота через webhook."""

    def __init__(self):
        """Инициализация сервера."""
        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None
        self.app: web.Application | None = None
        self.runner: web.AppRunner | None = None
        self.site: web.TCPSite | None = None
        self.settings = news_bot_settings
        self._shutdown_in_progress = False

        # Создаем приложение
        try:
            self._setup_app_base()
            self._setup_health_endpoints()
            logger.info("✅ Приложение создано")
        except Exception as e:
            logger.error(f"❌ Ошибка создания приложения: {e}", exc_info=True)

    async def init_bot(self) -> None:
        """Инициализация Bot и Dispatcher."""
        try:
            logger.info("🤖 Инициализация новостного бота...")

            # Создаем Bot
            self.bot = Bot(
                token=self.settings.news_bot_token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )

            # Создаем Dispatcher с Redis storage или MemoryStorage
            storage = await self._create_fsm_storage()
            self.dp = Dispatcher(storage=storage)

            # Регистрируем роутер новостного бота
            self.dp.include_router(news_bot_router)
            logger.info("✅ Роутер новостного бота зарегистрирован")

            logger.info("✅ Bot и Dispatcher инициализированы")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации бота: {e}")
            raise

    async def _create_fsm_storage(self):
        """Создать FSM storage с поддержкой Redis."""
        redis_url = os.getenv("REDIS_URL")

        if redis_url:
            try:
                redis_client = Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                )
                await redis_client.ping()
                storage = RedisStorage(redis=redis_client, state_ttl=86400, data_ttl=86400)
                logger.info("✅ FSM storage: Redis")
                return storage
            except Exception as e:
                logger.warning(f"⚠️ Redis недоступен: {e}, используем MemoryStorage")

        logger.info("📋 FSM storage: MemoryStorage")
        return MemoryStorage()

    async def setup_webhook(self) -> str:
        """Настройка webhook для Telegram."""
        try:
            webhook_url = f"https://{self.settings.news_bot_webhook_domain}/webhook/news"
            logger.info(f"🔗 Установка webhook: {webhook_url}")

            await self.bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
            )

            webhook_info = await self.bot.get_webhook_info()
            logger.info(f"✅ Webhook установлен: {webhook_info.url}")

            return webhook_url

        except Exception as e:
            logger.error(f"❌ Ошибка установки webhook: {e}")
            raise

    def _setup_app_base(self) -> None:
        """Создание базового aiohttp приложения."""
        logger.info("🌐 Создание веб-приложения...")

        self.app = web.Application(
            client_max_size=25 * 1024 * 1024,  # 25MB
        )

        self.app["bot"] = self.bot

    def _setup_health_endpoints(self) -> None:
        """Настройка health check endpoints."""

        async def health_check(_request: web.Request) -> web.Response:
            """Health check endpoint."""
            return web.json_response(
                {
                    "status": "ok",
                    "service": "news-bot",
                    "mode": "webhook",
                },
                status=200,
            )

        self.app.router.add_get("/health/news", health_check)
        self.app.router.add_get("/health", health_check)

    def _setup_webhook_handler(self) -> None:
        """Настройка webhook handler."""
        webhook_path = "/webhook/news"
        webhook_handler = SimpleRequestHandler(dispatcher=self.dp, bot=self.bot)
        webhook_handler.register(self.app, path=webhook_path)
        logger.info(f"📡 Webhook handler зарегистрирован на пути: {webhook_path}")

    async def start_early_server(self) -> None:
        """Запуск HTTP сервера ДО тяжелой инициализации."""
        try:
            port = int(os.getenv("PORT", "10000"))
            host = os.getenv("HOST", "0.0.0.0")

            logger.info(f"🏥 Запуск healthcheck сервера на {host}:{port}")

            self.runner = web.AppRunner(
                self.app,
                access_log=None,
                keepalive_timeout=75,
                enable_cleanup_closed=True,
            )
            await self.runner.setup()

            self.site = web.TCPSite(
                self.runner,
                host,
                port,
                backlog=1000,
                reuse_address=True,
                reuse_port=False,
            )
            await self.site.start()

            logger.info(f"✅ Сервер запущен на порту {port}")

        except Exception as e:
            logger.error(f"❌ Ошибка запуска сервера: {e}")
            raise

    async def startup_bot(self) -> None:
        """Инициализация бота (вызывается ДО запуска сервера)."""
        logger.info("🚀 Инициализация новостного бота...")

        # Инициализация базы данных
        await init_database()
        logger.info("📊 База данных инициализирована")

        # Инициализация бота
        await self.init_bot()

        # Обновляем bot в app context
        self.app["bot"] = self.bot

        # Добавляем webhook handler
        self._setup_webhook_handler()

    async def startup_services(self) -> None:
        """Инициализация сервисов (вызывается ПОСЛЕ запуска сервера)."""
        # Настройка webhook
        webhook_url = await self.setup_webhook()

        logger.info("✅ Сервер готов к работе")
        logger.info(f"🌐 Webhook URL: {webhook_url}")
        logger.info(f"🏥 Health check: https://{self.settings.news_bot_webhook_domain}/health/news")

    async def shutdown(self) -> None:
        """Остановка сервера."""
        if self._shutdown_in_progress:
            return

        self._shutdown_in_progress = True

        try:
            logger.info("🛑 Остановка сервера...")

            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()

            if self.bot:
                try:
                    await self.bot.delete_webhook(drop_pending_updates=False)
                    await self.bot.session.close()
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка закрытия бота: {e}")

            logger.info("✅ Сервер остановлен")

        except Exception as e:
            logger.error(f"❌ Ошибка остановки сервера: {e}")

    async def run(self) -> None:
        """Запуск основного цикла веб-сервера."""
        try:
            port = int(os.getenv("PORT", "10000"))
            host = os.getenv("HOST", "0.0.0.0")

            logger.info(f"✅ Веб-сервер полностью инициализирован на {host}:{port}")
            logger.info("📡 Ожидание обновлений от Telegram...")

            # Keep-alive пинг
            keep_alive_task = asyncio.create_task(self._keep_alive_ping(port))

            shutdown_event = asyncio.Event()

            def signal_handler():
                logger.info("🛑 Получен сигнал остановки...")
                shutdown_event.set()

            if sys.platform != "win32":
                try:
                    import signal

                    loop = asyncio.get_event_loop()
                    for sig in (signal.SIGTERM, signal.SIGINT):
                        loop.add_signal_handler(sig, signal_handler)
                except (NotImplementedError, RuntimeError):
                    pass

            try:
                await shutdown_event.wait()
            except KeyboardInterrupt:
                logger.info("🛑 Получен KeyboardInterrupt...")
            finally:
                keep_alive_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await keep_alive_task

        except Exception as e:
            logger.error(f"❌ Ошибка запуска веб-сервера: {e}")
            raise
        finally:
            await self.shutdown()

    async def _keep_alive_ping(self, port: int) -> None:
        """Keep-alive пинг для предотвращения засыпания контейнера."""
        import aiohttp

        await asyncio.sleep(5)

        logger.info("🔄 Keep-alive пинг запущен (каждые 4 минуты)")

        while True:
            try:
                await asyncio.sleep(240)

                async with (
                    aiohttp.ClientSession() as session,
                    session.get(f"http://localhost:{port}/health/news", timeout=5) as resp,
                ):
                    if resp.status == 200:
                        logger.debug("💓 Keep-alive ping OK")

            except asyncio.CancelledError:
                logger.info("🛑 Keep-alive пинг остановлен")
                break
            except Exception as e:
                logger.warning(f"⚠️ Keep-alive ping error: {e}")
                await asyncio.sleep(60)


async def main() -> None:
    """Главная функция запуска сервера."""
    server = NewsBotServer()

    try:
        # 1. Инициализация бота ДО запуска сервера
        await server.startup_bot()

        # 2. Запускаем HTTP сервер
        await server.start_early_server()

        # 3. Инициализация сервисов ПОСЛЕ запуска сервера
        await server.startup_services()

        # 4. Основной цикл
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
