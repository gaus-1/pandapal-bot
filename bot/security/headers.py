"""
Модуль заголовков безопасности для PandaPal Bot.
OWASP A05:2021 - Security Misconfiguration

Обеспечивает правильные HTTP заголовки безопасности:
- X-Frame-Options (защита от clickjacking)
- X-Content-Type-Options (защита от MIME sniffing)
- X-XSS-Protection (защита от XSS)
- Strict-Transport-Security (принуждение HTTPS)
- Referrer-Policy (контроль referrer)
- Permissions-Policy (контроль API браузера)
"""


class SecurityHeaders:
    """
    Класс для управления заголовками безопасности.

    Предоставляет набор заголовков для защиты от основных веб-уязвимостей
    и обеспечения конфиденциальности пользователей.
    """

    @staticmethod
    def get_security_headers() -> dict[str, str]:
        """
        Возвращает полный набор заголовков безопасности.

        Returns:
            Dict[str, str]: Словарь заголовков безопасности
        """
        return {
            # Защита от clickjacking
            "X-Frame-Options": "DENY",
            # Защита от MIME sniffing
            "X-Content-Type-Options": "nosniff",
            # Защита от XSS (для старых браузеров)
            "X-XSS-Protection": "1; mode=block",
            # Принуждение HTTPS (HSTS)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            # Контроль referrer информации
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # Контроль API браузера (для защиты детей)
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=(), "
                "payment=(), "
                "sync-xhr=()"
            ),
            # Дополнительная защита от clickjacking
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "https://telegram.org https://www.googletagmanager.com https://mc.yandex.ru; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws://localhost:* http://localhost:* "
                "https://api.pandapal.ru https://mc.yandex.ru "
                "https://region1.google-analytics.com https://www.google-analytics.com; "
                "frame-src 'self' https://mc.yandex.ru; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none';"
            ),
            # Контроль кеширования для безопасности
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            # Дополнительная защита
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }

    @staticmethod
    def get_csp_for_telegram_webapp() -> str:
        """
        Возвращает CSP специально для Telegram WebApp.

        Returns:
            str: Content Security Policy для Telegram WebApp
        """
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://telegram.org https://web.telegram.org; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https://api.pandapal.ru https://telegram.org; "
            "frame-src 'self' https://telegram.org; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'self' https://telegram.org;"
        )

    @staticmethod
    def get_minimal_headers() -> dict[str, str]:
        """
        Возвращает минимальный набор заголовков для API.

        Returns:
            Dict[str, str]: Минимальный набор заголовков
        """
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

    @staticmethod
    def validate_headers(headers: dict[str, str]) -> dict[str, bool]:
        """
        Проверяет корректность заголовков безопасности.

        Args:
            headers: Словарь заголовков для проверки

        Returns:
            Dict[str, bool]: Результаты проверки каждого заголовка
        """
        required_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Strict-Transport-Security",
            "Referrer-Policy",
        ]

        results = {}
        for header in required_headers:
            results[header] = header in headers and headers[header] is not None

        return results


# Утилиты для быстрого доступа
def get_standard_security_headers() -> dict[str, str]:
    """Получить стандартные заголовки безопасности."""
    return SecurityHeaders.get_security_headers()


def get_telegram_security_headers() -> dict[str, str]:
    """Получить заголовки безопасности для Telegram WebApp."""
    headers = SecurityHeaders.get_security_headers()
    headers["Content-Security-Policy"] = SecurityHeaders.get_csp_for_telegram_webapp()
    return headers


def get_api_security_headers() -> dict[str, str]:
    """Получить минимальные заголовки безопасности для API."""
    return SecurityHeaders.get_minimal_headers()
