#!/usr/bin/env python3
"""
Веб-сервер для запуска PandaPal Telegram бота через webhook.

Этот модуль инициализирует aiogram Bot и Dispatcher, настраивает webhook
для работы на Railway.app и запускает aiohttp сервер для приема обновлений
от Telegram.

ВАЖНО: Production-ready конфигурация для 24/7 работы.
- Webhook режим (не polling) для стабильности
- Автоматическая установка webhook при запуске
- Раздача React frontend из /dist
- Health check на /health
- Порт 8080 (Railway стандарт)

Основные компоненты:
- Инициализация Bot и Dispatcher
- Регистрация всех обработчиков из bot/handlers
- Настройка webhook для Railway.app
- HTTP сервер для приема webhook запросов
- Health check endpoints
- Интеграция метрик

Архитектура:
- SOLID принципы: разделение ответственности между инициализацией и запуском
- ООП: использование классов для организации кода
- PEP8: соблюдение стандартов кодирования
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
from aiogram.webhook.aiohttp_server import SimpleRequestHandler  # noqa: E402
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
        self.runner: web.AppRunner | None = None
        self.site: web.TCPSite | None = None
        self.settings = settings
        self._shutdown_in_progress = False

        # Создаем приложение сразу для раннего healthcheck
        try:
            self._setup_app_base()
            self._setup_health_endpoints()
            logger.info("✅ Базовое приложение создано для healthcheck")
        except Exception as e:
            logger.error(f"❌ Ошибка создания базового приложения: {e}", exc_info=True)

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

    def _setup_app_base(self) -> None:
        """
        Создание базового aiohttp приложения.

        Создает приложение с настройками размера запросов
        и добавляет bot в контекст приложения.
        """
        logger.info("🌐 Создание базового веб-приложения...")

        # Создаем приложение с увеличенным лимитом для больших запросов (фото, аудио)
        # По умолчанию aiohttp имеет лимит ~1MB, увеличиваем до 10MB для base64 медиа
        # Настройки для очень высокой нагрузки (1000+ одновременных запросов)
        # Примечание: limit и limit_per_host настраиваются через TCPSite backlog, не через Application
        self.app = web.Application(
            client_max_size=10 * 1024 * 1024,  # 10MB для медиа
        )

        # Добавляем bot в app context для использования в endpoints
        self.app["bot"] = self.bot

    def _setup_middleware(self) -> None:
        """
        Настройка middleware для приложения.

        Устанавливает security middleware и защиту от перегрузки.
        """
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
        """
        Настройка health check endpoints.

        Регистрирует быстрый и детальный health check endpoints.
        """

        async def health_check(_request: web.Request) -> web.Response:
            """
            Health check endpoint с проверкой компонентов.

            Быстрый ответ для Railway - сначала простой статус,
            затем асинхронно проверяем компоненты.
            """
            # Быстрый ответ для Railway (без блокирующих проверок)
            return web.json_response(
                {
                    "status": "ok",
                    "service": "pandapal-bot",
                    "mode": "webhook",
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

    def _register_api_route(self, module_path: str, setup_func_name: str, route_name: str) -> None:
        """
        Регистрация одного API роута.

        Args:
            module_path: Путь к модулю (например, 'bot.api.miniapp_endpoints')
            setup_func_name: Имя функции для установки (например, 'setup_miniapp_routes')
            route_name: Название роута для логирования (например, 'Mini App API')
        """
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
        """
        Настройка API маршрутов.

        Регистрирует все API endpoints для Mini App, Games, Premium и Auth.
        """
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
        """
        Настройка раздачи статических файлов frontend.

        Регистрирует маршруты для статических файлов, assets и SPA fallback.
        """
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
        """
        Настройка webhook handler.

        Регистрирует обработчик webhook для Telegram после всех маршрутов.
        """
        # Настраиваем webhook handler ПОСЛЕ регистрации всех маршрутов
        # Явно указываем путь /webhook для Railway
        webhook_path = "/webhook"
        webhook_handler = SimpleRequestHandler(dispatcher=self.dp, bot=self.bot)
        webhook_handler.register(self.app, path=webhook_path)
        logger.info(f"📡 Webhook handler зарегистрирован на пути: {webhook_path}")

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
        Создание aiohttp приложения.

        Создает веб-приложение с маршрутами для webhook,
        health check и метрик.

        Returns:
            web.Application: Настроенное веб-приложение
        """
        try:
            logger.info("🌐 Создание веб-приложения...")

            # Создание базового приложения
            self._setup_app_base()

            # Настройка health check endpoints ПЕРВЫМИ (для Railway healthcheck)
            self._setup_health_endpoints()

            # Настройка middleware
            self._setup_middleware()

            # Настройка API маршрутов
            self._setup_api_routes()

            # Настройка frontend статики
            self._setup_frontend_static()

            # Настройка webhook handler
            self._setup_webhook_handler()

            logger.info("✅ Веб-приложение создано")
            return self.app

        except Exception as e:
            logger.error(f"❌ Ошибка создания приложения: {e}")
            raise

    async def startup(self) -> None:
        """Запуск сервера - инициализация всех компонентов."""
        # Проверка Redis подключения
        await self._check_redis_connection()

        # Проверка Prometheus метрик
        self._check_prometheus_status()
        try:
            logger.info("🚀 Запуск PandaPal Bot Server...")

            # Инициализация базы данных
            await init_database()
            logger.info("📊 База данных инициализирована")

            # Инициализация SessionService (для персистентных сессий)
            from bot.services.session_service import get_session_service

            get_session_service()
            logger.info("🔐 SessionService инициализирован")

            # Инициализация бота
            await self.init_bot()

            # Запуск SimpleEngagementService для еженедельных напоминаний
            if self.bot:
                from bot.services.simple_engagement import SimpleEngagementService

                self.engagement_service = SimpleEngagementService(self.bot)
                await self.engagement_service.start()
                logger.info("⏰ SimpleEngagementService запущен")

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

            # Закрываем сессию бота
            if self.bot:
                try:
                    await self.bot.session.close()
                    logger.info("✅ Сессия бота закрыта")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка закрытия сессии бота: {e}")

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

            # Запускаем веб-сервер с настройками для высокой нагрузки
            self.runner = web.AppRunner(
                self.app,
                # Настройки для обработки высокой нагрузки
                access_log=None,  # Отключаем access log для производительности (опционально)
                keepalive_timeout=75,  # Keep-alive таймаут (увеличено с 30)
                enable_cleanup_closed=True,  # Автоматическая очистка закрытых соединений
            )
            await self.runner.setup()

            self.site = web.TCPSite(
                self.runner,
                host,
                port,
                # Настройки TCP для высокой нагрузки
                backlog=1000,  # Размер очереди ожидающих соединений (по умолчанию 128)
                reuse_address=True,  # Переиспользование адреса
                reuse_port=False,  # Не используем SO_REUSEPORT (может вызвать проблемы)
            )
            await self.site.start()

            logger.info(f"✅ Сервер запущен на порту {port}")
            logger.info(f"✅ Healthcheck доступен: http://{host}:{port}/health")

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
        """
        Keep-alive пинг для предотвращения засыпания контейнера на Railway Free.

        Пингует локальный /health endpoint каждые 4 минуты.
        """
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
