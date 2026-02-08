"""
Валидация Telegram Web App initData
Защита от подделки запросов к Mini App API

OWASP: A02:2021 - Cryptographic Failures
"""

import hashlib
import hmac
import time
from urllib.parse import parse_qsl

from loguru import logger

from bot.config import settings


class TelegramWebAppAuth:
    """
    Валидация данных из Telegram Mini App.

    Telegram подписывает initData используя HMAC-SHA256.
    Мы проверяем эту подпись чтобы убедиться что запрос пришел от Telegram.

    Спецификация: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """

    @staticmethod
    def validate_init_data(init_data: str) -> dict[str, str] | None:
        """
        Проверка подлинности initData от Telegram.

        Args:
            init_data: Строка initData из WebApp.initData

        Returns:
            Dict с данными пользователя или None если невалидно

        Raises:
            ValueError: При невалидных данных
        """
        try:
            if not init_data:
                logger.warning("🚫 initData пустой")
                return None

            # Парсим query string
            parsed = dict(parse_qsl(init_data, keep_blank_values=True))

            # Извлекаем hash (подпись Telegram)
            received_hash = parsed.pop("hash", None)
            if not received_hash:
                logger.warning("🚫 initData без hash")
                return None

            # Создаем строку для проверки (по спецификации Telegram)
            # Сортируем параметры и объединяем в формате key=value\n
            data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

            # Вычисляем secret_key = HMAC-SHA256(bot_token, "WebAppData")
            secret_key = hmac.new(
                key=b"WebAppData",
                msg=settings.telegram_bot_token.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()

            # Вычисляем hash = HMAC-SHA256(secret_key, data_check_string)
            calculated_hash = hmac.new(
                key=secret_key, msg=data_check_string.encode("utf-8"), digestmod=hashlib.sha256
            ).hexdigest()

            # Сравниваем (защита от timing attack через constant-time compare)
            if not hmac.compare_digest(received_hash, calculated_hash):
                logger.warning("🚫 Невалидная подпись initData")
                logger.debug(f"Expected: {calculated_hash}, Got: {received_hash}")
                return None

            # Проверяем auth_date (не старше 24 часов, не из будущего)
            auth_date = int(parsed.get("auth_date", "0"))
            current_time = int(time.time())

            if auth_date > current_time + 60:
                logger.warning(
                    f"🚫 initData из будущего: auth_date={auth_date}, now={current_time}"
                )
                return None

            if current_time - auth_date > 86400:
                logger.warning(f"🚫 initData устарел: {current_time - auth_date} секунд назад")
                return None

            logger.info("✅ Telegram initData валиден")
            logger.debug(f"Аутентифицирован пользователь: {parsed.get('user', 'unknown')}")

            return parsed

        except ValueError as e:
            logger.error(f"❌ Ошибка парсинга initData: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка валидации initData: {e}")
            return None

    @staticmethod
    def extract_user_data(validated_data: dict[str, str]) -> dict | None:
        """
        Извлечь данные пользователя из валидированного initData.

        Args:
            validated_data: Данные после валидации

        Returns:
            Dict с данными пользователя или None
        """
        try:
            import json

            user_json = validated_data.get("user")
            if not user_json:
                return None

            user_data = json.loads(user_json)

            return {
                "id": user_data.get("id"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "username": user_data.get("username"),
                "language_code": user_data.get("language_code"),
                "is_premium": user_data.get("is_premium", False),
            }

        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON пользователя: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения данных пользователя: {e}")
            return None
