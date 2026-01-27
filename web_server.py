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

from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.enums import ParseMode  # noqa: E402
from aiogram.fsm.storage.memory import MemoryStorage  # noqa: E402
from aiogram.fsm.storage.redis import RedisStorage  # noqa: E402
from aiogram.webhook.aiohttp_server import SimpleRequestHandler  # noqa: E402
from aiohttp import web  # noqa: E402
from loguru import logger  # noqa: E402
from redis.asyncio import Redis  # noqa: E402

from bot.config import settings  # noqa: E402
from bot.config.news_bot_settings import news_bot_settings  # noqa: E402
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
        self.news_bot_enabled = os.getenv("NEWS_BOT_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        self._shutdown_in_progress = False

        # Создаем приложение и добавляем ВСЕ роуты сразу (до запуска сервера)
        # После запуска сервера через AppRunner роутер "замораживается"
        try:
            self._setup_app_base()
            self._setup_health_endpoints()
            # Добавляем все роуты ДО запуска сервера
            self._setup_middleware()
            self._setup_api_routes()
            self._setup_frontend_static()
            # Webhook handler добавим после инициализации бота (до запуска сервера)
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

    def _setup_middleware(self) -> None:
        """Настройка middleware для приложения."""
        # Настраиваем security middleware ПЕРВЫМ (выполняется первым)
        try:
            from bot.security.middleware import setup_security_middleware

            setup_security_middleware(self.app)
            logger.info("🛡️ Security middleware зарегистрирован")
        except ImportError as e:
            logger.error(f"❌ Не удалось загрузить security middleware: {e}")
            raise

        # Добавляем защиту от перегрузки
        try:
            from bot.security.overload_protection import overload_protection_middleware

            self.app.middlewares.append(overload_protection_middleware)
            logger.info("✅ Защита от перегрузки активирована")
        except ImportError:
            logger.warning("⚠️ Защита от перегрузки недоступна")

        # Middleware для логирования webhook запросов
        @web.middleware
        async def webhook_logging_middleware(request: web.Request, handler):
            """Логирование всех запросов к webhook."""
            if request.path.startswith("/webhook"):
                logger.info(
                    f"📥 Webhook запрос: {request.method} {request.path}, "
                    f"IP={request.remote}, Headers={dict(request.headers)}"
                )
            return await handler(request)

        self.app.middlewares.append(webhook_logging_middleware)

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

    def _setup_health_endpoints(self) -> None:
        """Настройка health check endpoints."""

        async def health_check(_request: web.Request) -> web.Response:
            """Health check endpoint."""
            # Быстрый ответ для Railway (без блокирующих проверок)
            return web.json_response(
                {
                    "status": "ok",
                    "service": "pandapal-bot",
                    "mode": "webhook",
                },
                status=200,
            )

        async def test_news_webhook(_request: web.Request) -> web.Response:
            """Тестовый endpoint для проверки доступности /webhook/news."""
            return web.json_response(
                {
                    "status": "ok",
                    "path": "/webhook/news",
                    "message": "News bot webhook endpoint is accessible",
                    "bot_enabled": self.news_bot_enabled,
                    "bot_initialized": self.news_bot is not None,
                },
                status=200,
            )

        async def health_check_detailed(_request: web.Request) -> web.Response:
            """Детальный health check с проверкой всех компонентов."""
            components = {}
            overall_status = "ok"

            # Проверка бота
            bot_status, bot_data = await self._check_bot_health()
            components.update(bot_data)
            if bot_status == "error":
                overall_status = "error"
            elif bot_status == "degraded" and overall_status == "ok":
                overall_status = "degraded"

            bot_info = bot_data.get("bot_info")

            # Проверка базы данных
            db_status, db_data = self._check_database_health()
            components.update(db_data)
            if db_status == "error":
                overall_status = "error"

            # Проверка webhook
            webhook_status, webhook_data = await self._check_webhook_health()
            components.update(webhook_data)
            if webhook_status == "degraded" and overall_status == "ok":
                overall_status = "degraded"

            status_code = (
                200 if overall_status == "ok" else (503 if overall_status == "error" else 200)
            )

            return web.json_response(
                {
                    "status": overall_status,
                    "mode": "webhook",
                    "webhook_url": f"https://{self.settings.webhook_domain}/webhook",
                    "bot_username": bot_info.username if bot_info else None,
                    "components": components,
                },
                status=status_code,
            )

        # Регистрируем маршруты ДО setup_application
        # Быстрый health check для Railway (отвечает мгновенно)
        self.app.router.add_get("/health", health_check)
        # Детальный health check для мониторинга
        self.app.router.add_get("/health/detailed", health_check_detailed)
        # Тестовый endpoint для проверки новостного бота
        self.app.router.add_get("/test/news-webhook", test_news_webhook)

    def _register_api_route(self, module_path: str, setup_func_name: str, route_name: str) -> None:
        """Регистрация одного API роута."""
        try:
            module = __import__(module_path, fromlist=[setup_func_name])
            setup_func = getattr(module, setup_func_name)
            setup_func(self.app)
            logger.info(f"✅ {route_name} routes зарегистрированы")
        except ImportError as e:
            logger.warning(f"⚠️ Не удалось загрузить {route_name}: {e}")
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при регистрации {route_name}: {e}", exc_info=True)

    def _setup_api_routes(self) -> None:
        """Настройка API маршрутов."""
        # ВАЖНО: Регистрируем API роуты ПЕРЕД frontend (чтобы они имели приоритет)
        route_configs = [
            ("bot.api.miniapp", "setup_miniapp_routes", "🎮 Mini App API"),
            ("bot.api.games_endpoints", "setup_games_routes", "🎮 Games API"),
            ("bot.api.premium_endpoints", "setup_premium_routes", "💰 Premium API"),
            ("bot.api.auth_endpoints", "setup_auth_routes", "🔐 Auth API"),
        ]

        for module_path, setup_func, route_name in route_configs:
            self._register_api_route(module_path, setup_func, route_name)

        # Интегрируем метрики (если доступны)
        try:
            from bot.api.metrics_endpoint import add_metrics_to_web_server

            add_metrics_to_web_server(self.app)
            logger.info("📊 Метрики интегрированы в веб-сервер")
        except ImportError:
            logger.debug("📊 Метрики недоступны (опционально)")

    def _setup_frontend_static(self) -> None:
        """Настройка раздачи статических файлов frontend."""
        frontend_dist = Path(__file__).parent / "frontend" / "dist"
        if frontend_dist.exists():
            # Раздаем статические файлы из корня dist
            static_files = [
                "logo.png",  # Основной логотип
                "favicon.ico",  # Favicon для Яндекс (создается из logo.png)
                "robots.txt",
                "sitemap.xml",
                "security.txt",  # Security.txt для ответственного раскрытия уязвимостей
                "panda-happy.png",  # Веселая панда для игр
                "panda-sad.png",  # Грустная панда для игр
                "yandex_3f9e35f6d79cfb2f.html",  # Яндекс.Вебмастер верификация
            ]

            # Если favicon.ico нет, используем logo.png как favicon
            favicon_ico_path = frontend_dist / "favicon.ico"
            if not favicon_ico_path.exists():
                logo_png_path = frontend_dist / "logo.png"
                if logo_png_path.exists():
                    # Создаем симлинк или копируем logo.png как favicon.ico
                    import shutil

                    shutil.copy2(logo_png_path, favicon_ico_path)
                    logger.info("✅ Создан favicon.ico из logo.png")
            for static_file in static_files:
                file_path = frontend_dist / static_file
                if file_path.exists():
                    # Определяем MIME тип для статических файлов
                    content_type = "application/octet-stream"
                    if static_file.endswith(".svg"):
                        content_type = "image/svg+xml"
                    elif static_file.endswith(".png"):
                        content_type = "image/png"
                    elif static_file.endswith(".ico"):
                        content_type = "image/x-icon"
                    elif static_file.endswith(".json"):
                        content_type = "application/json"
                    elif static_file.endswith(".txt"):
                        content_type = "text/plain"
                    elif static_file.endswith(".xml"):
                        content_type = (
                            "text/xml; charset=utf-8"  # text/xml предпочтительнее для sitemap.xml
                        )
                    elif static_file.endswith(".js"):
                        content_type = "application/javascript"
                    elif static_file.endswith(".html"):
                        content_type = "text/html"

                    # Кэширование для статических файлов (кроме HTML)
                    # Используем замыкание с дефолтными аргументами для захвата переменных
                    async def serve_static_file(
                        _request: web.Request,
                        fp=file_path,
                        ct=content_type,
                        sf=static_file,
                    ) -> web.Response:
                        """Раздача статического файла с кэшированием."""
                        headers = {"Content-Type": ct}
                        # HTML не кэшируем (динамический контент)
                        if not sf.endswith(".html"):
                            headers["Cache-Control"] = "public, max-age=31536000, immutable"
                        return web.FileResponse(fp, headers=headers)

                    self.app.router.add_get(f"/{static_file}", serve_static_file)

            # Раздаем папку assets ПЕРЕД SPA fallback (важен порядок!)
            assets_dir = frontend_dist / "assets"
            if assets_dir.exists():
                # Универсальный обработчик для всех assets файлов
                async def serve_asset(request: web.Request) -> web.Response:
                    """Раздача любого файла из assets директории."""
                    filename = request.match_info.get("filename", "")
                    if not filename:
                        return web.Response(status=404, text="Asset filename required")

                    file_path = assets_dir / filename
                    if not file_path.exists() or not file_path.is_file():
                        # Логируем с информацией о доступных файлах для отладки
                        available_js = [f for f in os.listdir(assets_dir) if f.endswith(".js")]
                        logger.warning(
                            f"⚠️ Assets файл не найден: /assets/{filename} | "
                            f"Доступные JS: {', '.join(available_js[:3])}{'...' if len(available_js) > 3 else ''}"
                        )
                        return web.Response(status=404, text=f"Asset not found: {filename}")

                    # Определяем MIME тип
                    content_type = "application/octet-stream"
                    if filename.endswith(".js"):
                        content_type = "application/javascript"
                    elif filename.endswith(".css"):
                        content_type = "text/css"
                    elif filename.endswith(".map"):
                        content_type = "application/json"
                    elif filename.endswith(".png"):
                        content_type = "image/png"
                    elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
                        content_type = "image/jpeg"
                    elif filename.endswith(".svg"):
                        content_type = "image/svg+xml"
                    elif filename.endswith(".woff") or filename.endswith(".woff2"):
                        content_type = "font/woff2"
                    elif filename.endswith(".webp"):
                        content_type = "image/webp"

                    # Кэширование для статических ресурсов (хэшированные имена файлов)
                    headers = {"Content-Type": content_type}
                    if any(
                        filename.endswith(ext)
                        for ext in [
                            ".js",
                            ".css",
                            ".woff",
                            ".woff2",
                            ".png",
                            ".jpg",
                            ".jpeg",
                            ".webp",
                            ".svg",
                        ]
                    ):
                        headers["Cache-Control"] = "public, max-age=31536000, immutable"

                    return web.FileResponse(file_path, headers=headers)

                # Регистрируем универсальный роут для всех assets
                self.app.router.add_get("/assets/{filename:.*}", serve_asset)

                # Логируем все найденные файлы для отладки
                all_files = os.listdir(assets_dir)
                js_files = [f for f in all_files if f.endswith(".js")]
                logger.info(f"✅ Assets директория зарегистрирована: {assets_dir}")
                logger.info(f"📦 Найдено файлов в assets: {len(all_files)}")
                logger.info(f"📦 Найдено JS файлов: {len(js_files)}")
                if js_files:
                    logger.info(
                        f"📦 JS файлы: {', '.join(js_files[:5])}{'...' if len(js_files) > 5 else ''}"
                    )

            # Security.txt по стандартному пути /.well-known/security.txt
            security_txt_path = frontend_dist / "security.txt"
            if security_txt_path.exists():

                async def serve_security_txt(_request: web.Request) -> web.Response:
                    """Раздача security.txt по стандартному пути."""
                    return web.FileResponse(
                        security_txt_path,
                        headers={"Content-Type": "text/plain; charset=utf-8"},
                    )

                self.app.router.add_get("/.well-known/security.txt", serve_security_txt)
                logger.info("✅ Security.txt зарегистрирован по пути /.well-known/security.txt")

            # Главная страница
            self.app.router.add_get("/", lambda _: web.FileResponse(frontend_dist / "index.html"))

            # SPA Fallback - все неизвестные роуты возвращают index.html
            # НО исключаем /api, /assets, /webhook, /health, /.well-known
            async def spa_fallback(request: web.Request) -> web.Response:
                path = request.path
                # Исключаем API, assets, webhook, health, .well-known из SPA fallback
                # Проверяем ТОЧНО, чтобы не перехватывать assets
                if (
                    path.startswith("/api/")
                    or path.startswith("/assets/")
                    or path == "/webhook"
                    or path.startswith("/webhook/")
                    or path == "/health"
                    or path.startswith("/health/")
                    or path.startswith("/.well-known/")
                ):
                    # Логируем 404 для assets для отладки
                    if path.startswith("/assets/"):
                        logger.warning(f"⚠️ Assets файл не найден: {path}")
                    return web.Response(status=404, text="Not Found")
                return web.FileResponse(frontend_dist / "index.html")

            # Регистрируем fallback ПОСЛЕДНИМ (после всех API и static routes)
            # Используем простой паттерн - проверка пути внутри функции
            self.app.router.add_get("/{tail:.*}", spa_fallback)

            logger.info(f"✅ Frontend настроен: {frontend_dist}")
        else:
            # Fallback - если frontend не собран
            async def root_handler(_request: web.Request) -> web.Response:
                # Используем простой health check для fallback
                return web.json_response(
                    {
                        "status": "ok",
                        "service": "pandapal-bot",
                        "mode": "webhook",
                    },
                    status=200,
                )

            self.app.router.add_get("/", root_handler)
            logger.warning("⚠️ Frontend не найден, используется fallback")

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

            # Регистрируем роутер новостного бота
            from bot.handlers.news_bot import router as news_bot_router

            self.news_dp.include_router(news_bot_router)
            logger.info("✅ Роутер новостного бота зарегистрирован")

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

        # Настройка webhook основного бота
        webhook_url = await self.setup_webhook()

        # Настройка webhook новостного бота (если включен)
        if self.news_bot_enabled and self.news_bot:
            try:
                await self.setup_news_bot_webhook()
            except Exception as e:
                logger.error(
                    f"❌ Критическая ошибка установки webhook новостного бота: {e}", exc_info=True
                )
                # Отключаем бот, если не удалось установить webhook
                self.news_bot_enabled = False

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

            await self.news_bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query", "inline_query"],
            )

            webhook_info = await self.news_bot.get_webhook_info()
            logger.info(f"✅ Webhook новостного бота установлен: {webhook_info.url}")
            logger.info(f"📊 Webhook info: {webhook_info}")

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
        """Keep-alive пинг для предотвращения засыпания контейнера."""
        import aiohttp

        await asyncio.sleep(5)  # Даем серверу 5 сек на полный запуск

        logger.info("🔄 Keep-alive пинг запущен (каждые 4 минуты)")

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
