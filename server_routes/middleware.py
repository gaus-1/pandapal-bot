"""
Регистрация middleware для aiohttp приложения.

Security, overload protection, логирование запросов.
"""

from aiohttp import web
from loguru import logger


def setup_middleware(app: web.Application) -> None:
    """Настройка middleware для приложения."""
    try:
        from bot.security.middleware import setup_security_middleware

        setup_security_middleware(app)
        logger.info("🛡️ Security middleware зарегистрирован")
    except ImportError as e:
        logger.error(f"❌ Не удалось загрузить security middleware: {e}")
        raise

    try:
        from bot.security.overload_protection import overload_protection_middleware

        app.middlewares.append(overload_protection_middleware)
        logger.info("✅ Защита от перегрузки активирована")
    except ImportError:
        logger.warning("⚠️ Защита от перегрузки недоступна")

    @web.middleware
    async def request_logging_middleware(request: web.Request, handler):
        """Логирование всех входящих запросов для диагностики."""
        if request.path.startswith("/webhook"):
            ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.remote
            user_agent = request.headers.get("User-Agent", "N/A")[:100]
            content_type = request.headers.get("Content-Type", "N/A")
            logger.info(
                f"📥 [EARLY] Webhook запрос: {request.method} {request.path}, IP={ip}, "
                f"Content-Type={content_type}, UA={user_agent[:50]}"
            )

        try:
            response = await handler(request)
            if request.path.startswith("/webhook"):
                logger.info(f"📤 [EARLY] Webhook ответ: {request.path}, status={response.status}")
            return response
        except Exception as e:
            logger.error(f"❌ [EARLY] Ошибка обработки webhook {request.path}: {e}", exc_info=True)
            raise

    app.middlewares.insert(0, request_logging_middleware)

    @web.middleware
    async def compression_middleware(request: web.Request, handler):
        """Gzip-сжатие текстовых ответов для уменьшения размера передачи."""
        response = await handler(request)

        # Забираем Content-Type
        content_type = getattr(response, "content_type", "") or response.headers.get(
            "Content-Type", ""
        )
        compressible_ext = (
            "text/html",
            "text/css",
            "text/plain",
            "text/xml",
            "application/javascript",
            "application/json",
            "application/xml",
            "image/svg+xml",
        )
        # Принудительно сжимаем, игнорируя Accept-Encoding, так как Railway Edge proxy может его вырезать,
        # оставляя нас без сжатия при отдаче SPA index.html (из-за no-cache прокси сам не может его сжать).
        if (
            content_type
            and any(ct in content_type for ct in compressible_ext)
            and hasattr(response, "enable_compression")
        ):
            response.enable_compression(web.ContentCoding.gzip)

        return response

    app.middlewares.append(compression_middleware)
    logger.info("✅ Gzip compression middleware активирован")
