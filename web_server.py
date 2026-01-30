#!/usr/bin/env python3
"""
Веб-сервер для запуска PandaPal Telegram бота через webhook.

Инициализирует aiogram Bot и Dispatcher, настраивает webhook для Railway.app
и запускает aiohttp сервер для приема обновлений от Telegram.
"""

import asyncio
import contextlib
import os
import sys
from pathlib import Path

# Добавляем корневую папку в PYTHONPATH ПЕРЕД импортами
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Loguru в stdout до импорта bot.* — чтобы в Railway все логи шли в [inf], не в [err]
from loguru import logger  # noqa: E402

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=os.environ.get("LOG_LEVEL", "INFO"),
)

from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.enums import ParseMode  # noqa: E402
from aiogram.fsm.storage.memory import MemoryStorage  # noqa: E402
from aiogram.fsm.storage.redis import RedisStorage  # noqa: E402
from aiogram.webhook.aiohttp_server import SimpleRequestHandler  # noqa: E402
from aiohttp import web  # noqa: E402
from redis.asyncio import Redis  # noqa: E402

from bot.config import settings  # noqa: E402
from bot.config.news_bot_settings import news_bot_settings  # noqa: E402
from bot.database import init_database  # noqa: E402
from bot.handlers import routers  # noqa: E402
from server_routes import (  # noqa: E402
    setup_api_routes,
    setup_frontend_static,
    setup_health_routes,
    setup_middleware,
)

# Отключить новостной бот и сбор новостей (Mini App и сайт не трогаем)
NEWS_BOT_DISABLED = (
    True  # True = выключено, False = по env NEWS_BOT_ENABLED / NEWS_COLLECTION_ENABLED
)


class PandaPalBotServer:
    """Сервер для запуска PandaPal Telegram бота через webhook."""

    def __init__(self):
        """Инициализация сервера."""
        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None
        self.news_bot: Bot | None = None
        self.news_dp: Dispatcher | None = None
        self.app: web.Application | None = None
        self.runner: web.AppRunner | None = None
        self.site: web.TCPSite | None = None
        self.settings = settings
        # Новостной бот: включен ли Telegram-бот и webhook
        env_enabled = os.getenv("NEWS_BOT_ENABLED", "false").lower() in ("true", "1", "yes")
        settings_enabled = news_bot_settings.news_bot_enabled
        self.news_bot_enabled = env_enabled or settings_enabled

        # Сбор новостей в БД: работает при NEWS_BOT_ENABLED или NEWS_COLLECTION_ENABLED
        env_collection = os.getenv("NEWS_COLLECTION_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        self.news_collection_enabled = (
            self.news_bot_enabled or env_collection or news_bot_settings.news_collection_enabled
        )
        if NEWS_BOT_DISABLED:
            self.news_bot_enabled = False
            self.news_collection_enabled = False
            logger.info("📰 Новостной бот отключен по флагу NEWS_BOT_DISABLED")

        if self.news_bot_enabled:
            logger.info(
                f"📰 Новостной бот включен (env={env_enabled}, settings={settings_enabled})"
            )
        else:
            logger.info("📰 Новостной бот отключен")
        if self.news_collection_enabled:
            logger.info("📰 Сбор новостей в БД включен")
        else:
            logger.info(
                "📰 Сбор новостей в БД отключен (NEWS_BOT_ENABLED или NEWS_COLLECTION_ENABLED=true чтобы включить)"
            )
        self._shutdown_in_progress = False

        # Создаем приложение и добавляем ВСЕ роуты сразу (до запуска сервера)
        try:
            self._setup_app_base()
            setup_health_routes(self.app, self)
            setup_middleware(self.app)
            setup_api_routes(self.app)
            setup_frontend_static(self.app, root_dir)
            logger.info("✅ Приложение создано со всеми роутами (webhook добавим позже)")
        except Exception as e:
            logger.error(f"❌ Ошибка создания приложения: {e}", exc_info=True)

    async def init_bot(self) -> None:
        """Инициализация Bot и Dispatcher."""
        try:
            logger.info("🤖 Инициализация Telegram бота...")

            # Создаем Bot с настройками по умолчанию
            self.bot = Bot(
                token=self.settings.telegram_bot_token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )

            # Создаем Dispatcher с Redis storage для горизонтального масштабирования
            # Fallback на MemoryStorage если Redis недоступен
            storage = await self._create_fsm_storage()
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

    async def _create_fsm_storage(self):
        """
        Создать FSM storage с поддержкой Redis для горизонтального масштабирования.

        Returns:
            RedisStorage или MemoryStorage в зависимости от доступности Redis
        """
        redis_url = os.getenv("REDIS_URL")

        if redis_url:
            try:
                # Пытаемся подключиться к Redis
                redis_client = Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                )

                # Проверяем подключение
                await redis_client.ping()

                # Создаем Redis storage для FSM
                storage = RedisStorage(redis=redis_client, state_ttl=86400, data_ttl=86400)
                logger.info("✅ FSM storage: Redis (горизонтальное масштабирование поддерживается)")
                return storage

            except Exception as e:
                logger.warning(f"⚠️ Redis недоступен для FSM: {e}, используем MemoryStorage")

        # Fallback на MemoryStorage
        logger.info("📋 FSM storage: MemoryStorage (только один инстанс)")
        return MemoryStorage()

    async def setup_webhook(self) -> str:
        """Настройка webhook для Telegram."""
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

    def _setup_app_base(self) -> None:
        """Создание базового aiohttp приложения."""
        logger.info("🌐 Создание базового веб-приложения...")

        # Создаем приложение с увеличенным лимитом для больших запросов (фото, аудио)
        # По умолчанию aiohttp ~1MB. Фото base64 ~1.33× размера; 25MB даёт запас для крупных снимков.
        self.app = web.Application(
            client_max_size=25 * 1024 * 1024,  # 25MB для медиа (фото, аудио)
        )

        # Добавляем bot в app context для использования в endpoints
        self.app["bot"] = self.bot

    async def _check_bot_health(self) -> tuple[str, dict]:
        """Проверка здоровья бота."""
        if not self.bot:
            return "error", {"bot": "not_initialized"}

        try:
            bot_info = await self.bot.get_me()
            return "ok", {"bot": "ok", "bot_info": bot_info}
        except Exception as bot_error:
            logger.warning("⚠️ Не удалось получить информацию о боте: %s", bot_error)
            return "degraded", {"bot": "error"}

    def _check_database_health(self) -> tuple[str, dict]:
        """Проверка здоровья базы данных."""
        try:
            from sqlalchemy import text

            from bot.database import engine

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return "ok", {"database": "ok"}
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return "error", {"database": "error"}

    async def _check_webhook_health(self) -> tuple[str, dict]:
        """Проверка здоровья webhook."""
        if not self.bot:
            return "degraded", {"webhook": "not_available"}

        try:
            webhook_info = await self.bot.get_webhook_info()
            if not webhook_info.url:
                return "degraded", {"webhook": "not_set"}
            return "ok", {"webhook": "ok"}
        except Exception as e:
            logger.warning(f"⚠️ Webhook check failed: {e}")
            return "degraded", {"webhook": "error"}

    def _setup_webhook_handler(self) -> None:
        """Настройка webhook handler после инициализации бота."""
        # Основной бот
        webhook_path = "/webhook"
        webhook_handler = SimpleRequestHandler(dispatcher=self.dp, bot=self.bot)
        webhook_handler.register(self.app, path=webhook_path)
        logger.info(f"📡 Webhook handler зарегистрирован на пути: {webhook_path}")

        # Новостной бот (если включен)
        if self.news_bot_enabled and self.news_bot and self.news_dp:
            news_webhook_path = "/webhook/news"

            news_webhook_handler = SimpleRequestHandler(dispatcher=self.news_dp, bot=self.news_bot)
            news_webhook_handler.register(self.app, path=news_webhook_path)
            logger.info(f"📡 News bot webhook handler зарегистрирован на пути: {news_webhook_path}")
            logger.info(f"📋 News bot token: {news_bot_settings.news_bot_token[:15]}...")

            # Проверяем, что роут действительно зарегистрирован
            routes = [str(route) for route in self.app.router.routes()]
            news_routes = [r for r in routes if "/webhook/news" in r]
            if news_routes:
                logger.info(f"✅ Роут /webhook/news найден в зарегистрированных: {news_routes}")
            else:
                logger.error("❌ Роут /webhook/news НЕ найден в зарегистрированных роутах!")
                logger.info(f"📋 Все webhook роуты: {[r for r in routes if 'webhook' in r]}")
        else:
            logger.warning(
                f"⚠️ News bot webhook handler НЕ зарегистрирован: "
                f"enabled={self.news_bot_enabled}, bot={self.news_bot is not None}, dp={self.news_dp is not None}"
            )

    async def start_early_server(self) -> None:
        """
        Запуск минимального HTTP сервера с /health ДО тяжелой инициализации.

        Это критично для Railway healthcheck - сервер должен отвечать
        на /health в течение 30 секунд после старта контейнера.
        """
        try:
            port = int(os.getenv("PORT", "10000"))
            host = os.getenv("HOST", "0.0.0.0")

            logger.info(f"🏥 Запуск раннего healthcheck сервера на {host}:{port}")

            # Создаем и запускаем runner с базовым приложением (уже имеет /health)
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

            logger.info(f"✅ Ранний healthcheck сервер запущен на порту {port}")
            logger.info("🏥 /health доступен для Railway healthcheck")

        except Exception as e:
            logger.error(f"❌ Ошибка запуска раннего сервера: {e}")
            raise

    async def _check_redis_connection(self) -> None:
        """Проверка подключения к Redis и логирование статуса."""
        try:
            from bot.services.cache_service import cache_service

            # Пытаемся подключиться к Redis
            if cache_service._redis_client:
                try:
                    await cache_service._ensure_redis_connection()
                    if cache_service._use_redis:
                        stats = await cache_service.get_stats()
                        logger.info(
                            f"✅ Redis подключен: {stats.get('type', 'unknown')}, "
                            f"connected={stats.get('connected', False)}"
                        )
                    else:
                        logger.warning(
                            "⚠️ Redis URL указан, но подключение не установлено (используется in-memory кэш)"
                        )
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка проверки Redis: {e}")
            else:
                redis_url = getattr(self.settings, "redis_url", "")
                if redis_url:
                    logger.warning(f"⚠️ Redis URL указан, но клиент не создан: {redis_url[:50]}...")
                else:
                    logger.info("📋 Redis URL не указан, используется in-memory кэш")
        except Exception as e:
            logger.error(f"❌ Ошибка проверки Redis: {e}")

    def _check_prometheus_status(self) -> None:
        """Проверка статуса Prometheus метрик."""
        try:
            import os

            prometheus_enabled = os.getenv("PROMETHEUS_METRICS_ENABLED", "true").lower() not in (
                "false",
                "0",
                "no",
                "off",
            )

            if prometheus_enabled:
                logger.info("📊 Prometheus метрики включены")
            else:
                logger.info(
                    "📊 Prometheus метрики отключены (установите PROMETHEUS_METRICS_ENABLED=true для включения)"
                )
        except Exception as e:
            logger.warning(f"⚠️ Ошибка проверки Prometheus: {e}")

    def create_app(self) -> web.Application:
        """
        Обратная совместимость - все роуты уже добавлены в __init__.

        Этот метод больше не используется, роуты добавляются до запуска сервера.
        """
        return self.app

    async def startup_bot(self) -> None:
        """Инициализация бота (вызывается ДО запуска сервера)."""
        # Проверка Redis подключения
        await self._check_redis_connection()

        # Проверка Prometheus метрик
        self._check_prometheus_status()

        logger.info("🚀 Инициализация PandaPal Bot...")

        # Инициализация базы данных
        await init_database()
        logger.info("📊 База данных инициализирована")

        # Инициализация SessionService (для персистентных сессий)
        from bot.services.session_service import get_session_service

        get_session_service()
        logger.info("🔐 SessionService инициализирован")

        # Инициализация основного бота
        await self.init_bot()

        # Обновляем bot в app context (был None при создании app в __init__)
        self.app["bot"] = self.bot

        # Инициализация новостного бота (если включен)
        if self.news_bot_enabled:
            await self.init_news_bot()

        # Добавляем webhook handlers (ДО запуска сервера, чтобы роутер не был заморожен)
        self._setup_webhook_handler()

    async def init_news_bot(self) -> None:
        """Инициализация новостного бота."""
        try:
            logger.info("📰 Инициализация новостного бота...")

            # Проверяем токен
            if not news_bot_settings.news_bot_token:
                logger.error("❌ NEWS_BOT_TOKEN не установлен, новостной бот отключен")
                self.news_bot_enabled = False
                return

            # Создаем Bot для новостей
            self.news_bot = Bot(
                token=news_bot_settings.news_bot_token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )

            # Создаем Dispatcher для новостного бота
            storage = await self._create_fsm_storage()
            self.news_dp = Dispatcher(storage=storage)

            # Добавляем middleware для логирования обновлений
            from aiogram import BaseMiddleware
            from aiogram.types import CallbackQuery, Message

            class NewsBotLoggingMiddleware(BaseMiddleware):
                """Middleware для логирования всех обновлений новостного бота."""

                async def __call__(self, handler, event, data):
                    """Логирование обновлений."""
                    update_type = type(event).__name__
                    logger.info(f"📰 News bot update received: type={update_type}")

                    if isinstance(event, Message):
                        user_id = event.from_user.id if event.from_user else "unknown"
                        text = event.text[:50] if event.text else "non-text"
                        logger.info(f"📰 News bot message: user={user_id}, text={text}")
                    elif isinstance(event, CallbackQuery):
                        user_id = event.from_user.id if event.from_user else "unknown"
                        cb_data = event.data[:50] if event.data else "no-data"
                        logger.info(f"📰 News bot callback: user={user_id}, data={cb_data}")

                    return await handler(event, data)

            # Регистрируем роутер новостного бота
            from bot.handlers.news_bot import router as news_bot_router

            # Логируем обработчики в роутере ДО включения
            logger.info(
                f"📰 News bot router handlers: message={len(news_bot_router.message.handlers)}, callback_query={len(news_bot_router.callback_query.handlers)}"
            )

            self.news_dp.include_router(news_bot_router)
            logger.info("✅ Роутер новостного бота зарегистрирован")

            # Добавляем middleware для логирования ПОСЛЕ регистрации роутера
            self.news_dp.message.middleware(NewsBotLoggingMiddleware())
            self.news_dp.callback_query.middleware(NewsBotLoggingMiddleware())

            # В aiogram 3.x обработчики остаются в роутере, не копируются в dispatcher
            # Это нормальное поведение - dispatcher использует обработчики через роутер
            logger.info(
                f"📰 News bot router handlers: message={len(news_bot_router.message.handlers)}, callback_query={len(news_bot_router.callback_query.handlers)}"
            )

            # Проверяем, что бот работает
            bot_info = await self.news_bot.get_me()
            logger.info(
                f"✅ Новостной бот инициализирован: @{bot_info.username} ({bot_info.first_name})"
            )
            logger.info(f"📋 Токен: {news_bot_settings.news_bot_token[:10]}...")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации новостного бота: {e}", exc_info=True)
            # Не прерываем запуск основного бота
            self.news_bot_enabled = False
            self.news_bot = None
            self.news_dp = None

    async def startup_services(self) -> None:
        """Инициализация сервисов (вызывается ПОСЛЕ запуска сервера)."""
        # Запуск SimpleEngagementService для еженедельных напоминаний
        if self.bot:
            from bot.services.simple_engagement import SimpleEngagementService

            self.engagement_service = SimpleEngagementService(self.bot)
            await self.engagement_service.start()
            logger.info("⏰ SimpleEngagementService запущен")

        # Запуск автоматического сбора новостей (если включен бот или только сбор)
        if self.news_collection_enabled:
            asyncio.create_task(self._check_and_collect_news_on_startup())
            asyncio.create_task(self._news_collection_loop())
            logger.info("📰 Автоматический сбор новостей запущен")

        # Настройка webhook основного бота
        webhook_url = await self.setup_webhook()

        # Настройка webhook новостного бота (если включен)
        if self.news_bot_enabled and self.news_bot:
            try:
                # Пробуем установить webhook с повторными попытками
                max_retries = 3
                for attempt in range(1, max_retries + 1):
                    try:
                        await self.setup_news_bot_webhook()
                        # Проверяем, что webhook действительно установлен
                        webhook_info = await self.news_bot.get_webhook_info()
                        if webhook_info.url:
                            logger.info(
                                f"✅ Webhook новостного бота успешно установлен (попытка {attempt})"
                            )
                            break
                        else:
                            logger.warning(
                                f"⚠️ Webhook не установлен после попытки {attempt}, повторяем..."
                            )
                            if attempt < max_retries:
                                await asyncio.sleep(2)
                    except Exception as e:
                        logger.warning(
                            f"⚠️ Ошибка установки webhook (попытка {attempt}/{max_retries}): {e}"
                        )
                        if attempt < max_retries:
                            await asyncio.sleep(2)
                        else:
                            raise
            except Exception as e:
                logger.error(
                    f"❌ Критическая ошибка установки webhook новостного бота после {max_retries} попыток: {e}",
                    exc_info=True,
                )
                # НЕ отключаем бот - возможно webhook установится позже
                logger.warning(
                    "⚠️ Новостной бот будет работать, но webhook нужно установить вручную"
                )

        logger.info("✅ Сервер готов к работе")
        logger.info(f"🌐 Webhook URL: {webhook_url}")
        if self.news_bot_enabled:
            logger.info(f"📰 News bot webhook: https://{self.settings.webhook_domain}/webhook/news")
        logger.info(f"🏥 Health check: https://{self.settings.webhook_domain}/health")

    async def setup_news_bot_webhook(self) -> str:
        """Настройка webhook для новостного бота."""
        try:
            if not self.news_bot:
                logger.error("❌ News bot не инициализирован, невозможно установить webhook")
                return ""

            # Используем тот же домен, что и основной бот
            webhook_domain = self.settings.webhook_domain
            webhook_url = f"https://{webhook_domain}/webhook/news"
            logger.info(f"🔗 Установка webhook новостного бота: {webhook_url}")
            logger.info(f"📋 Токен новостного бота: {news_bot_settings.news_bot_token[:10]}...")

            # Принудительно удаляем старый webhook перед установкой нового
            try:
                await self.news_bot.delete_webhook(drop_pending_updates=True)
                logger.info("🗑️ Старый webhook новостного бота удален")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка удаления старого webhook (может не существовать): {e}")

            # Небольшая задержка перед установкой нового webhook
            await asyncio.sleep(0.5)

            await self.news_bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query", "inline_query"],
            )

            webhook_info = await self.news_bot.get_webhook_info()
            logger.info(f"✅ Webhook новостного бота установлен: {webhook_info.url}")
            logger.info(
                f"📊 Webhook info: url={webhook_info.url}, "
                f"pending={webhook_info.pending_update_count}, "
                f"last_error={webhook_info.last_error_message}, "
                f"last_error_date={webhook_info.last_error_date}, "
                f"ip_address={webhook_info.ip_address}, "
                f"max_connections={webhook_info.max_connections}, "
                f"allowed_updates={webhook_info.allowed_updates}"
            )

            # КРИТИЧНО: Проверяем, что webhook действительно установлен
            if not webhook_info.url or webhook_info.url != webhook_url:
                logger.error(
                    f"❌ КРИТИЧНО: Webhook новостного бота НЕ установлен правильно! "
                    f"Ожидали: {webhook_url}, Получили: {webhook_info.url}"
                )
                raise RuntimeError(f"Webhook новостного бота не установлен: {webhook_info.url}")
            else:
                logger.info(f"✅ Webhook URL совпадает: {webhook_info.url}")

            # Проверяем ошибки
            if webhook_info.last_error_message:
                logger.error(
                    f"❌ Ошибка webhook новостного бота: {webhook_info.last_error_message} "
                    f"(дата: {webhook_info.last_error_date})"
                )
            else:
                logger.info("✅ Ошибок webhook нет")

            # Проверяем pending updates
            if webhook_info.pending_update_count > 0:
                logger.warning(
                    f"⚠️ Есть {webhook_info.pending_update_count} ожидающих обновлений для новостного бота"
                )
            else:
                logger.info("✅ Ожидающих обновлений нет")

            # Дополнительная диагностика
            if webhook_info.url != webhook_url:
                logger.error(
                    f"❌ КРИТИЧНО: Webhook URL не совпадает! "
                    f"Ожидали: {webhook_url}, Получили: {webhook_info.url}"
                )
            if webhook_info.last_error_message:
                logger.error(
                    f"❌ Ошибка webhook новостного бота: {webhook_info.last_error_message} "
                    f"(дата: {webhook_info.last_error_date})"
                )
            if webhook_info.pending_update_count > 0:
                logger.warning(
                    f"⚠️ Есть {webhook_info.pending_update_count} ожидающих обновлений для новостного бота"
                )

            return webhook_url

        except Exception as e:
            logger.error(f"❌ Ошибка установки webhook новостного бота: {e}", exc_info=True)
            raise

    async def shutdown(self) -> None:
        """Остановка сервера - очистка ресурсов."""
        # Предотвращаем двойной вызов shutdown
        if self._shutdown_in_progress:
            logger.debug("⚠️ Shutdown уже выполняется, пропускаем повторный вызов")
            return

        self._shutdown_in_progress = True

        try:
            logger.info("🛑 Остановка сервера...")

            # Останавливаем веб-сервер
            # Сначала останавливаем site, затем очищаем runner
            site_to_stop = self.site
            runner_to_cleanup = self.runner

            # Сбрасываем ссылки сразу, чтобы избежать повторных вызовов
            self.site = None
            self.runner = None

            if site_to_stop:
                try:
                    await site_to_stop.stop()
                    logger.info("✅ TCP site остановлен")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка остановки TCP site: {e}")

            if runner_to_cleanup:
                try:
                    await runner_to_cleanup.cleanup()
                    logger.info("✅ AppRunner очищен")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка очистки AppRunner: {e}")

            # Останавливаем SimpleEngagementService
            if hasattr(self, "engagement_service") and self.engagement_service:
                try:
                    await self.engagement_service.stop()
                    logger.info("✅ SimpleEngagementService остановлен")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка остановки SimpleEngagementService: {e}")

            # Удаляем webhook (опционально, для чистоты)
            if self.bot:
                try:
                    await self.bot.delete_webhook(drop_pending_updates=False)
                    logger.info("✅ Webhook удален")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка удаления webhook: {e}")

            # Удаляем webhook новостного бота
            if self.news_bot:
                try:
                    await self.news_bot.delete_webhook(drop_pending_updates=False)
                    logger.info("✅ Webhook новостного бота удален")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка удаления webhook новостного бота: {e}")

            # Закрываем сессии ботов
            if self.bot:
                try:
                    await self.bot.session.close()
                    logger.info("✅ Сессия бота закрыта")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка закрытия сессии бота: {e}")

            if self.news_bot:
                try:
                    await self.news_bot.session.close()
                    logger.info("✅ Сессия новостного бота закрыта")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка закрытия сессии новостного бота: {e}")

            logger.info("✅ Сервер остановлен")

        except Exception as e:
            logger.error(f"❌ Ошибка остановки сервера: {e}")

    async def run(self) -> None:
        """Запуск основного цикла веб-сервера (сервер уже запущен в start_early_server)."""
        try:
            port = int(os.getenv("PORT", "10000"))
            host = os.getenv("HOST", "0.0.0.0")

            # Сервер уже запущен в start_early_server(), здесь только логируем и ждем
            logger.info(f"✅ Веб-сервер полностью инициализирован на {host}:{port}")

            # Проверяем, что healthcheck действительно работает
            try:
                import aiohttp

                async with (
                    aiohttp.ClientSession() as session,
                    session.get(f"http://localhost:{port}/health", timeout=2) as resp,
                ):
                    if resp.status == 200:
                        logger.info("✅ Healthcheck проверен локально - работает!")
                    else:
                        logger.warning(f"⚠️ Healthcheck вернул статус {resp.status}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось проверить healthcheck локально: {e}")

            logger.info("📡 Ожидание обновлений от Telegram...")

            # Запускаем keep-alive пинг в фоне (для Railway Free)
            keep_alive_task = asyncio.create_task(self._keep_alive_ping(port))

            # Создаем Event для graceful shutdown
            shutdown_event = asyncio.Event()

            # Обработка сигналов для graceful shutdown
            def signal_handler():
                logger.info("🛑 Получен сигнал остановки, начинаем graceful shutdown...")
                shutdown_event.set()

            # Регистрируем обработчики сигналов (только на Unix системах)
            if sys.platform != "win32":
                try:
                    import signal

                    loop = asyncio.get_event_loop()
                    for sig in (signal.SIGTERM, signal.SIGINT):
                        loop.add_signal_handler(sig, signal_handler)
                except (NotImplementedError, RuntimeError):
                    # Если сигналы не поддерживаются, используем KeyboardInterrupt
                    pass

            # Ждем сигнала остановки или KeyboardInterrupt
            try:
                await shutdown_event.wait()
            except KeyboardInterrupt:
                logger.info("🛑 Получен KeyboardInterrupt, останавливаем сервер...")
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
        """Keep-alive пинг для предотвращения засыпания контейнера и проверка webhook."""
        import aiohttp

        await asyncio.sleep(5)  # Даем серверу 5 сек на полный запуск

        logger.info("🔄 Keep-alive пинг запущен (каждые 4 минуты)")

        # Запускаем проверку webhook новостного бота в фоне
        if self.news_bot_enabled and self.news_bot:
            asyncio.create_task(self._check_news_bot_webhook_periodically())

        while True:
            try:
                await asyncio.sleep(240)  # 4 минуты

                async with (
                    aiohttp.ClientSession() as session,
                    session.get(f"http://localhost:{port}/health", timeout=5) as resp,
                ):
                    if resp.status == 200:
                        logger.debug("💓 Keep-alive ping OK")
                    else:
                        logger.warning(f"⚠️ Keep-alive ping failed: {resp.status}")

            except asyncio.CancelledError:
                logger.info("🛑 Keep-alive пинг остановлен")
                break
            except Exception as e:
                logger.warning(f"⚠️ Keep-alive ping error: {e}")
                await asyncio.sleep(60)  # При ошибке ждем 1 минуту и пробуем снова

    async def _check_news_bot_webhook_periodically(self) -> None:
        """Периодическая проверка и переустановка webhook новостного бота."""
        await asyncio.sleep(10)  # Ждем 10 сек после старта для первой проверки

        # Первая проверка сразу после старта
        try:
            if self.news_bot_enabled and self.news_bot:
                webhook_info = await self.news_bot.get_webhook_info()
                expected_url = f"https://{self.settings.webhook_domain}/webhook/news"
                if not webhook_info.url or webhook_info.url != expected_url:
                    logger.warning(
                        f"⚠️ Webhook новостного бота не установлен при старте! "
                        f"Ожидали: {expected_url}, Получили: {webhook_info.url or 'пусто'}"
                    )
                    logger.info("🔗 Устанавливаем webhook...")
                    await self.setup_news_bot_webhook()
        except Exception as e:
            logger.error(f"❌ Ошибка проверки webhook при старте: {e}", exc_info=True)

        logger.info("🔄 Запущена периодическая проверка webhook новостного бота (каждые 2 минуты)")

        while True:
            try:
                await asyncio.sleep(120)  # Проверяем каждые 2 минуты

                if not self.news_bot_enabled or not self.news_bot:
                    break

                webhook_info = await self.news_bot.get_webhook_info()
                expected_url = f"https://{self.settings.webhook_domain}/webhook/news"

                if not webhook_info.url or webhook_info.url != expected_url:
                    logger.warning(
                        f"⚠️ Webhook новостного бота сброшен! "
                        f"Ожидали: {expected_url}, Получили: {webhook_info.url or 'пусто'}"
                    )
                    logger.info("🔗 Переустанавливаем webhook...")

                    try:
                        await self.setup_news_bot_webhook()
                        webhook_info = await self.news_bot.get_webhook_info()
                        if webhook_info.url == expected_url:
                            logger.info("✅ Webhook новостного бота успешно переустановлен")
                        else:
                            logger.error(
                                f"❌ Не удалось переустановить webhook: {webhook_info.url}"
                            )
                    except Exception as e:
                        logger.error(f"❌ Ошибка переустановки webhook: {e}", exc_info=True)
                else:
                    logger.debug(f"✅ Webhook новостного бота в порядке: {webhook_info.url}")

            except asyncio.CancelledError:
                logger.info("🛑 Периодическая проверка webhook остановлена")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка проверки webhook: {e}", exc_info=True)
                await asyncio.sleep(60)  # При ошибке ждем минуту перед следующей попыткой

    async def _check_and_collect_news_on_startup(self) -> None:
        """При старте всегда запускаем сбор, чтобы бот был с новостями."""
        try:
            await asyncio.sleep(2)  # Короткая пауза для инициализации БД

            from bot.database import get_db
            from bot.services.news.repository import NewsRepository

            with get_db() as db:
                repo = NewsRepository(db)
                news_count = repo.count_all()

            if news_count < 50:
                logger.info(f"📰 В БД {news_count} новостей, запускаю сбор при старте...")
                await self._collect_news_now()
            else:
                logger.info(
                    f"📰 В БД уже {news_count} новостей, дозаполняю при старте для свежести"
                )
                await self._collect_news_now()
        except Exception as e:
            logger.error(f"❌ Ошибка проверки новостей при старте: {e}", exc_info=True)

    async def _news_collection_loop(self) -> None:
        """Фоновая задача: первый сбор через 5 мин, далее каждые 15 мин."""
        first_run = True
        while True:
            try:
                if first_run:
                    logger.info("📰 Первый периодический сбор новостей через 5 мин")
                    await asyncio.sleep(300)  # 5 мин до первого сбора
                    first_run = False
                else:
                    logger.info("📰 Следующий сбор новостей через 15 мин")
                    await asyncio.sleep(900)  # 15 мин

                await self._collect_news_now()

            except asyncio.CancelledError:
                logger.info("🛑 Автоматический сбор новостей остановлен")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле сбора новостей: {e}", exc_info=True)
                await asyncio.sleep(900)

    async def _collect_news_now(self) -> None:
        """Выполнить сбор новостей прямо сейчас."""
        if not self.news_collection_enabled:
            return

        try:
            logger.info("📰 Начинаю сбор новостей...")
            from bot.services.news.sources.humor_site_source import HumorSiteSource
            from bot.services.news.sources.joke_api_source import JokeAPISource
            from bot.services.news.sources.lenta_ru_source import LentaRuSource
            from bot.services.news.sources.local_humor_source import LocalHumorSource
            from bot.services.news.sources.newsapi_source import NewsAPISource
            from bot.services.news.sources.rbc_rss_source import RbcRssSource
            from bot.services.news.sources.web_scraper_source import WebScraperNewsSource
            from bot.services.news.sources.world_news_api_source import WorldNewsAPISource
            from bot.services.news_collector_service import NewsCollectorService

            # Lenta первым — больше новостей с Lenta.ru в ленте
            sources = [
                RbcRssSource(),
                LentaRuSource(),
                WorldNewsAPISource(),
                NewsAPISource(),
                WebScraperNewsSource(),
                HumorSiteSource(),
                JokeAPISource(),
                LocalHumorSource(),
            ]

            collector = NewsCollectorService(sources=sources)
            total_collected = await collector.collect_news(limit_per_source=15)
            await collector.close()

            logger.info(f"✅ Сбор новостей завершен: собрано {total_collected} новостей")
        except Exception as e:
            logger.error(f"❌ Ошибка сбора новостей: {e}", exc_info=True)


async def main() -> None:
    """Главная функция запуска сервера."""
    server = PandaPalBotServer()

    try:
        # 1. Инициализация бота (БД, бот) ДО запуска сервера
        # Это нужно чтобы добавить webhook handler до "заморозки" роутера
        await server.startup_bot()

        # 2. Запускаем HTTP сервер (роутер "замораживается" после этого)
        await server.start_early_server()

        # 3. Инициализация сервисов (webhook setup, services) ПОСЛЕ запуска сервера
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
