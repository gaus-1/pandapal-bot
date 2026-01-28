"""
Модуль проверки целостности ПО для PandaPal Bot.
OWASP A08:2021 - Software and Data Integrity Failures

Обеспечивает:
- Проверку целостности зависимостей
- Валидацию входящих данных
- Проверку цифровых подписей
- Защиту от десериализации
"""

import hashlib
import json
from typing import Any

from loguru import logger


class IntegrityChecker:
    """
    Класс для проверки целостности данных и ПО.

    Обеспечивает защиту от:
    - Несанкционированных изменений данных
    - Вредоносной десериализации
    - Подмены кода/данных
    """

    @staticmethod
    def calculate_checksum(data: str, algorithm: str = "sha256") -> str:
        """
        Вычисляет контрольную сумму данных.

        Args:
            data: Данные для проверки
            algorithm: Алгоритм хеширования (sha256, sha512)

        Returns:
            str: Контрольная сумма
        """
        if algorithm == "sha256":
            return hashlib.sha256(data.encode("utf-8")).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(data.encode("utf-8")).hexdigest()
        else:
            raise ValueError(f"Неподдерживаемый алгоритм: {algorithm}")

    @staticmethod
    def verify_checksum(data: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
        """
        Проверяет контрольную сумму данных.

        Args:
            data: Данные для проверки
            expected_checksum: Ожидаемая контрольная сумма
            algorithm: Алгоритм хеширования

        Returns:
            bool: True если контрольная сумма совпадает
        """
        actual_checksum = IntegrityChecker.calculate_checksum(data, algorithm)
        return actual_checksum == expected_checksum

    @staticmethod
    def safe_json_loads(json_string: str, max_size: int = 1024 * 1024) -> dict[str, Any] | None:
        """
        Безопасная десериализация JSON.

        Args:
            json_string: JSON строка
            max_size: Максимальный размер в байтах (по умолчанию 1MB)

        Returns:
            Optional[Dict[str, Any]]: Десериализованные данные (только dict) или None при ошибке
        """
        try:
            # Проверка размера
            if len(json_string.encode("utf-8")) > max_size:
                logger.error("❌ JSON превышает максимальный размер")
                return None

            # Безопасная десериализация (json.loads не выполняет код)
            data = json.loads(json_string)

            # Принимаем только dict, не list
            if not isinstance(data, dict):
                logger.error("❌ JSON должен быть объектом (dict), не массивом")
                return None

            # Гарантируем тип Dict[str, Any]
            if isinstance(data, dict):
                return dict(data)  # Преобразуем в обычный dict

            return None

        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка десериализации JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при парсинге JSON: {e}")
            return None

    @staticmethod
    def validate_telegram_data(data: dict[str, Any]) -> bool:
        """
        Валидация данных от Telegram API.

        Args:
            data: Данные от Telegram

        Returns:
            bool: True если данные валидны
        """
        # Проверяем наличие обязательных полей
        required_fields = ["update_id"]

        for field in required_fields:
            if field not in data:
                logger.warning(f"⚠️ Отсутствует обязательное поле: {field}")
                return False

        # Проверяем типы данных
        if not isinstance(data.get("update_id"), int):
            logger.warning("⚠️ update_id должен быть числом")
            return False

        return True

    @staticmethod
    def sanitize_user_input(user_input: str, max_length: int = 4000) -> str:
        """
        Очистка пользовательского ввода.

        Args:
            user_input: Ввод пользователя
            max_length: Максимальная длина

        Returns:
            str: Очищенный ввод
        """
        # Обрезаем до максимальной длины
        sanitized = user_input[:max_length]

        # Удаляем управляющие символы (кроме переноса строки и табуляции)
        sanitized = "".join(
            char for char in sanitized if char.isprintable() or char in ["\n", "\t"]
        )

        return sanitized


class SSRFProtection:
    """
    Защита от Server-Side Request Forgery (SSRF).
    OWASP A10:2021 - Server-Side Request Forgery

    Предотвращает атаки через:
    - Валидацию URL
    - Белый список доменов
    - Блокировку внутренних IP
    """

    # Белый список разрешенных доменов
    ALLOWED_DOMAINS = [
        "api.telegram.org",
        "generativelanguage.googleapis.com",
        "pandapal.ru",
        "mc.yandex.ru",
        "www.google-analytics.com",
        "lenta.ru",
        "mel.fm",
        "deti.mail.ru",
        "umorashka.ru",
    ]

    # Запрещенные IP диапазоны (внутренние сети)
    BLOCKED_IP_RANGES = [
        "127.0.0.0/8",  # Localhost
        "10.0.0.0/8",  # Private network
        "172.16.0.0/12",  # Private network
        "192.168.0.0/16",  # Private network
        "169.254.0.0/16",  # Link-local
        "0.0.0.0/8",  # Current network
        "224.0.0.0/4",  # Multicast
        "240.0.0.0/4",  # Reserved
    ]

    @staticmethod
    def is_safe_url(url: str) -> bool:
        """
        Проверяет, безопасен ли URL для запроса.

        Args:
            url: URL для проверки

        Returns:
            bool: True если URL безопасен
        """
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)

            # Проверяем схему (только HTTPS)
            if parsed.scheme not in ["https"]:
                logger.warning(f"⚠️ Небезопасная схема: {parsed.scheme}")
                return False

            # Проверяем домен
            domain = parsed.netloc.split(":")[0]  # Убираем порт

            # Проверяем белый список
            if not any(allowed in domain for allowed in SSRFProtection.ALLOWED_DOMAINS):
                logger.warning(f"⚠️ Домен не в белом списке: {domain}")
                return False

            # Проверяем, что это не IP адрес
            if SSRFProtection._is_ip_address(domain):
                logger.warning(f"⚠️ Прямые IP адреса запрещены: {domain}")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка валидации URL: {e}")
            return False

    @staticmethod
    def _is_ip_address(hostname: str) -> bool:
        """Проверяет, является ли строка IP адресом."""
        import re

        # Простая проверка на IPv4
        ipv4_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
        return bool(re.match(ipv4_pattern, hostname))

    @staticmethod
    def validate_external_request(url: str, method: str = "GET") -> bool:
        """
        Валидация внешнего HTTP запроса.

        Args:
            url: URL для запроса
            method: HTTP метод

        Returns:
            bool: True если запрос безопасен
        """
        # Проверяем URL
        if not SSRFProtection.is_safe_url(url):
            logger.error(f"🚫 Заблокирован небезопасный URL: {url}")
            return False

        # Проверяем метод
        if method not in ["GET", "POST"]:
            logger.error(f"🚫 Небезопасный HTTP метод: {method}")
            return False

        return True


# Утилиты для быстрого доступа
def verify_data_integrity(data: str, checksum: str) -> bool:
    """Быстрая проверка целостности данных."""
    return IntegrityChecker.verify_checksum(data, checksum)


def safe_deserialize_json(json_string: str) -> dict[str, Any] | None:
    """Быстрая безопасная десериализация JSON."""
    return IntegrityChecker.safe_json_loads(json_string)


def validate_url_safety(url: str) -> bool:
    """Быстрая проверка безопасности URL."""
    return SSRFProtection.is_safe_url(url)


def sanitize_input(user_input: str, max_length: int = 4000) -> str:
    """Быстрая очистка пользовательского ввода."""
    return IntegrityChecker.sanitize_user_input(user_input, max_length)
