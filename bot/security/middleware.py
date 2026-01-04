"""
Security middleware для aiohttp приложения.

Защита от:
- DDoS атак (rate limiting)
- CSRF атак (origin/referer validation)
- XSS (security headers)
- Injection (input validation)

OWASP Top 10 2021 compliance.
"""

import asyncio
import time
import uuid
from collections import defaultdict
from typing import Dict, Optional, Set, Tuple
from urllib.parse import urlparse

from aiohttp import web
from loguru import logger

from bot.config import settings
from bot.security.audit_logger import SecurityEventSeverity, SecurityEventType, log_security_event


class RateLimiter:
    """
    Rate limiter для защиты от DDoS атак.

    Использует sliding window алгоритм для отслеживания запросов.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Инициализация rate limiter.

        Args:
            max_requests: Максимальное количество запросов
            window_seconds: Временное окно в секундах
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Храним временные метки запросов по IP
        self._requests: Dict[str, list] = defaultdict(list)
        # Блокированные IP (временная блокировка)
        self._blocked: Dict[str, float] = {}
        # Время блокировки в секундах
        self._block_duration = 300  # 5 минут

    def _cleanup_old_requests(self, ip: str, current_time: float) -> None:
        """Удалить старые запросы из окна."""
        cutoff = current_time - self.window_seconds
        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

    def _cleanup_blocked(self, current_time: float) -> None:
        """Удалить истекшие блокировки."""
        expired = [ip for ip, block_time in self._blocked.items() if current_time > block_time]
        for ip in expired:
            del self._blocked[ip]

    def is_allowed(self, ip: str) -> Tuple[bool, Optional[str]]:
        """
        Проверить, разрешен ли запрос.

        Args:
            ip: IP адрес клиента

        Returns:
            (allowed, reason): Разрешен ли запрос и причина если нет
        """
        current_time = time.time()

        # Проверяем блокировку
        self._cleanup_blocked(current_time)
        if ip in self._blocked:
            return False, "IP temporarily blocked due to excessive requests"

        # Очищаем старые запросы
        self._cleanup_old_requests(ip, current_time)

        # Проверяем лимит
        request_count = len(self._requests[ip])
        if request_count >= self.max_requests:
            # Блокируем IP на 5 минут
            self._blocked[ip] = current_time + self._block_duration
            log_security_event(
                SecurityEventType.RATE_LIMIT_EXCEEDED,
                f"Rate limit exceeded for IP {ip}",
                SecurityEventSeverity.WARNING,
                metadata={"ip": ip, "requests": request_count},
            )
            return False, f"Rate limit exceeded: {request_count}/{self.max_requests} requests"

        # Регистрируем запрос
        self._requests[ip].append(current_time)
        return True, None


# Глобальные rate limiters для разных типов endpoints
# Увеличены лимиты для нормальной работы в продакшене
_rate_limiter_api = RateLimiter(
    max_requests=300, window_seconds=60
)  # 300 req/min для API (было 60)
_rate_limiter_auth = RateLimiter(
    max_requests=20, window_seconds=60
)  # 20 req/min для auth (было 10)
_rate_limiter_ai = RateLimiter(
    max_requests=100, window_seconds=60
)  # 100 req/min для AI (было 30, только для бесплатных)


def get_rate_limiter(path: str) -> Optional[RateLimiter]:
    """
    Получить подходящий rate limiter для пути.

    Args:
        path: Путь запроса

    Returns:
        RateLimiter: Подходящий limiter
    """
    if "/auth" in path:
        return _rate_limiter_auth
    elif "/ai/chat" in path:
        return _rate_limiter_ai
    else:
        return _rate_limiter_api


# Разрешенные origins для CSRF protection
ALLOWED_ORIGINS: Set[str] = {
    "https://pandapal.ru",
    "https://web.telegram.org",
    "https://telegram.org",
    "https://web.telegram.org:443",  # С портом
    "https://telegram.org:443",  # С портом
}

# Разрешенные referers
ALLOWED_REFERERS: Set[str] = {
    "https://pandapal.ru",
    "https://web.telegram.org",
    "https://telegram.org",
    "https://web.telegram.org:443",
    "https://telegram.org:443",
}


def validate_origin(request: web.Request) -> Tuple[bool, Optional[str]]:
    """
    Проверить Origin/Referer для CSRF protection.

    Args:
        request: HTTP запрос

    Returns:
        (valid, reason): Валиден ли origin и причина если нет
    """
    # Исключаем GET запросы и health check
    if request.method == "GET" or request.path in ["/health", "/webhook"]:
        return True, None

    # Для Telegram Mini App endpoints проверяем наличие initData в теле запроса
    # Это дополнительная проверка, что запрос от Telegram
    if request.path.startswith("/api/miniapp/"):
        # Пытаемся прочитать тело запроса для проверки initData
        # Но не читаем полностью, чтобы не блокировать поток
        try:
            # Проверяем Content-Type
            content_type = request.headers.get("Content-Type", "")
            if "application/json" in content_type:
                # Для Mini App endpoints разрешаем, если есть JSON body
                # Детальная проверка initData будет в самом endpoint
                return True, None
        except Exception as e:
            logger.debug("Ошибка проверки content-type: %s", e)

    origin = request.headers.get("Origin")
    referer = request.headers.get("Referer")

    # Если нет ни Origin ни Referer - проверяем другие признаки Telegram
    if not origin and not referer:
        # Telegram Mini App может не отправлять Origin, проверяем User-Agent
        user_agent = request.headers.get("User-Agent", "").lower()
        if "telegram" in user_agent:
            return True, None

        # Проверяем, может быть это запрос от Telegram Mini App (по пути)
        if request.path.startswith("/api/miniapp/"):
            # Для Mini App endpoints разрешаем, если нет явных признаков атаки
            return True, None

        return False, "Missing Origin and Referer headers"

    # Проверяем Origin (нормализуем - убираем порт если стандартный)
    if origin:
        parsed = urlparse(origin)
        # Убираем стандартные порты из сравнения
        netloc = parsed.netloc
        if netloc.endswith(":443") and parsed.scheme == "https":
            netloc = netloc[:-4]
        elif netloc.endswith(":80") and parsed.scheme == "http":
            netloc = netloc[:-3]

        origin_netloc = f"{parsed.scheme}://{netloc}"
        if origin_netloc not in ALLOWED_ORIGINS:
            # Для Mini App endpoints более мягкая проверка
            if request.path.startswith("/api/miniapp/"):
                # Разрешаем, если это похоже на Telegram домен
                if "telegram" in netloc.lower():
                    return True, None
            return False, f"Invalid Origin: {origin_netloc}"

    # Проверяем Referer (нормализуем - убираем порт если стандартный)
    if referer:
        parsed = urlparse(referer)
        # Убираем стандартные порты из сравнения
        netloc = parsed.netloc
        if netloc.endswith(":443") and parsed.scheme == "https":
            netloc = netloc[:-4]
        elif netloc.endswith(":80") and parsed.scheme == "http":
            netloc = netloc[:-3]

        referer_netloc = f"{parsed.scheme}://{netloc}"
        if referer_netloc not in ALLOWED_REFERERS:
            # Для Mini App endpoints более мягкая проверка
            if request.path.startswith("/api/miniapp/"):
                # Разрешаем, если это похоже на Telegram домен
                if "telegram" in netloc.lower():
                    return True, None
            return False, f"Invalid Referer: {referer_netloc}"

    return True, None


async def security_middleware(app: web.Application, handler):
    """
    Главный security middleware.

    Применяет:
    - Rate limiting
    - CSRF protection
    - Security headers
    - Request ID для tracing
    """

    async def middleware_handler(request: web.Request) -> web.Response:
        # Генерируем request ID для tracing
        request_id = str(uuid.uuid4())
        request["request_id"] = request_id

        # Получаем IP адрес
        # Проверяем X-Forwarded-For (для прокси/Cloudflare)
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not ip:
            ip = request.headers.get("X-Real-IP", "")
        if not ip:
            ip = request.remote

        request["client_ip"] = ip

        # Rate limiting (исключаем статические файлы, webhook, мини-апп)
        # Для AI endpoints rate limiting проверяется в самом endpoint с учетом premium
        # Здесь применяем только базовый IP-based rate limiting для защиты от DDoS
        excluded_paths = [
            "/webhook",  # Telegram webhook
            "/ai/chat",  # AI chat (своя логика rate limiting)
            "/health",  # Health check
            "/metrics",  # Metrics endpoint
        ]

        # Исключаем статические файлы (CSS, JS, images, fonts, etc.)
        static_extensions = [
            ".css",
            ".js",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".ico",
            ".woff",
            ".woff2",
            ".ttf",
            ".eot",
            ".map",
        ]
        is_static_file = any(request.path.endswith(ext) for ext in static_extensions)

        # Исключаем мини-апп endpoints (они имеют свою логику rate limiting)
        is_miniapp_endpoint = request.path.startswith("/api/miniapp/")

        # Применяем rate limiting только к API endpoints (не мини-апп и не статика)
        if (
            not any(request.path.startswith(excluded) for excluded in excluded_paths)
            and not is_static_file
            and not is_miniapp_endpoint
            and request.path.startswith("/api/")
        ):
            rate_limiter = get_rate_limiter(request.path)
            if rate_limiter:
                allowed, reason = rate_limiter.is_allowed(ip)
                if not allowed:
                    logger.warning(
                        f"🚫 Rate limit exceeded: IP={ip}, Path={request.path}, Reason={reason}"
                    )
                    log_security_event(
                        SecurityEventType.RATE_LIMIT_EXCEEDED,
                        f"Rate limit exceeded: {request.path}",
                        SecurityEventSeverity.WARNING,
                        metadata={"ip": ip, "path": request.path, "reason": reason},
                    )
                    return web.json_response(
                        {
                            "error": "Rate limit exceeded. Please try again later.",
                            "request_id": request_id,
                        },
                        status=429,
                        headers={"Retry-After": "60"},
                    )

        # Логируем ВСЕ запросы к API для отладки
        if request.path.startswith("/api/"):
            origin = request.headers.get("Origin", "N/A")
            referer = request.headers.get("Referer", "N/A")
            user_agent = request.headers.get("User-Agent", "N/A")[:100]
            logger.info(
                f"📥 API запрос: {request.method} {request.path}, IP={ip}, Origin={origin}, Referer={referer}, UA={user_agent}"
            )

        # CSRF protection (только для API endpoints)
        if request.path.startswith("/api/"):

            valid, reason = validate_origin(request)
            if not valid:
                origin = request.headers.get("Origin", "N/A")
                referer = request.headers.get("Referer", "N/A")
                logger.warning(
                    f"🚫 CSRF protection: Invalid origin/referer: IP={ip}, Path={request.path}, "
                    f"Origin={origin}, Referer={referer}, Reason={reason}"
                )
                log_security_event(
                    SecurityEventType.AUTHENTICATION_FAILURE,
                    f"CSRF protection triggered: {request.path}",
                    SecurityEventSeverity.WARNING,
                    metadata={"ip": ip, "path": request.path, "reason": reason},
                )
                return web.json_response(
                    {"error": "Invalid request origin", "request_id": request_id},
                    status=403,
                )

        # Выполняем запрос
        try:
            response = await handler(request)
        except Exception as e:
            logger.error(
                f"❌ Error in request handler: {e}",
                exc_info=True,
                extra={"request_id": request_id, "ip": ip, "path": request.path},
            )
            # Возвращаем generic error без деталей
            return web.json_response(
                {"error": "Internal server error", "request_id": request_id},
                status=500,
            )

        # Добавляем security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        # X-Frame-Options: разрешаем встраивание для Telegram (нужно для Mini App на ПК)
        # Используем SAMEORIGIN вместо DENY, чтобы Telegram Web мог встроить сайт в iframe
        # Дополнительная защита через CSP frame-ancestors
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS только для HTTPS
        if request.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Content-Security-Policy с разрешением встраивания для Telegram
        # frame-ancestors контролирует, кто может встроить страницу в iframe
        # Разрешаем только Telegram домены для Mini App
        csp_frame_ancestors = (
            "frame-ancestors 'self' https://web.telegram.org https://telegram.org;"
        )

        # Для API endpoints - более строгий CSP
        if request.path.startswith("/api/"):
            response.headers["Content-Security-Policy"] = (
                f"default-src 'self'; {csp_frame_ancestors}"
            )
        else:
            # Для frontend (Mini App) - разрешаем встраивание в Telegram
            # 'unsafe-inline' нужен для inline скриптов в index.html (подавление ошибок Telegram WebView)
            # https://mc.yandex.ru нужен для Яндекс.Метрики
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://telegram.org https://web.telegram.org https://mc.yandex.ru; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                f"connect-src 'self' https://api.pandapal.ru https://mc.yandex.ru; "
                f"{csp_frame_ancestors} "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests;"
            )

        # Request ID для tracing
        response.headers["X-Request-ID"] = request_id

        return response

    return middleware_handler


def setup_security_middleware(app: web.Application) -> None:
    """
    Настроить security middleware для приложения.

    Args:
        app: aiohttp приложение
    """
    # Регистрируем middleware ПЕРВЫМ (выполняется первым)
    app.middlewares.append(security_middleware)
    logger.info("🛡️ Security middleware настроен")
