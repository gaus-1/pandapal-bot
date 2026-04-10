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

        # FileResponse — потоковый ответ, у него нет атрибута body.
        # aiohttp сам умеет сжимать FileResponse через enable_compression().
        # Пропускаем любые ответы без атрибута body (FileResponse, StreamResponse).
        if isinstance(response, web.FileResponse):
            return response

        # Проверяем что клиент поддерживает gzip
        accept_encoding = request.headers.get("Accept-Encoding", "")
        if "gzip" not in accept_encoding:
            return response

        # Сжимаем только текстовые ответы
        content_type = response.headers.get("Content-Type", "")
        compressible_types = (
            "text/html",
            "text/css",
            "text/plain",
            "text/xml",
            "application/javascript",
            "application/xml",
            "image/svg+xml",
        )
        if not any(ct in content_type for ct in compressible_types):
            return response

        # Не сжимаем уже сжатые или маленькие ответы
        if response.headers.get("Content-Encoding"):
            return response

        body = getattr(response, "body", None)
        if body is None or len(body) < 1024:
            return response

        import zlib

        compressed = zlib.compress(body, level=6, wbits=16 + zlib.MAX_WBITS)

        # Сжатие имеет смысл только если результат меньше оригинала
        if len(compressed) >= len(body):
            return response

        response.body = compressed
        response.headers["Content-Encoding"] = "gzip"
        response.headers["Vary"] = "Accept-Encoding"
        if "Content-Length" in response.headers:
            response.headers["Content-Length"] = str(len(compressed))

        return response

    app.middlewares.append(compression_middleware)
    logger.info("✅ Gzip compression middleware активирован")
