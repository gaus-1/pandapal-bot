"""
Сервис для аутентификации через Telegram Login Widget.

Обеспечивает проверку подлинности данных от Telegram Login Widget
и управление сессиями пользователей на веб-сайте.
"""

import hashlib
import hmac
from datetime import UTC, datetime, timedelta

from loguru import logger

from bot.config import settings


class TelegramAuthService:
    """
    Сервис аутентификации через Telegram Login Widget.

    Обеспечивает:
    - Валидацию данных от Telegram (проверка hash)
    - Создание/обновление пользователей в БД
    - Безопасность авторизации
    """

    @staticmethod
    def validate_telegram_auth(auth_data: dict) -> bool:
        """
        Проверить подлинность данных от Telegram Login Widget.

        Алгоритм проверки (по официальной документации Telegram):
        1. Создаем строку data_check_string из всех полей кроме hash
        2. Вычисляем secret_key = SHA256(bot_token)
        3. Вычисляем HMAC-SHA256(data_check_string, secret_key)
        4. Сравниваем с полученным hash

        Args:
            auth_data: Данные от Telegram Login Widget (id, first_name, hash, etc)

        Returns:
            bool: True если данные валидны, False иначе

        Raises:
            ValueError: Если отсутствуют обязательные поля
        """
        # Проверяем обязательные поля
        if "hash" not in auth_data or "id" not in auth_data:
            logger.warning("⚠️ Отсутствуют обязательные поля в auth_data")
            return False

        received_hash = auth_data.pop("hash")

        # Проверяем срок действия (не старше 24 часов)
        auth_date = auth_data.get("auth_date")
        if auth_date:
            try:
                auth_datetime = datetime.fromtimestamp(int(auth_date), tz=UTC)
                if datetime.now(UTC) - auth_datetime > timedelta(hours=24):
                    logger.warning("⚠️ Данные авторизации устарели (>24 часов)")
                    return False
            except (ValueError, OSError) as e:
                logger.warning(f"⚠️ Неверный формат auth_date: {e}")
                return False

        # Создаем data_check_string
        # Сортируем параметры по ключу и объединяем в строку key=value
        data_check_string = "\n".join(
            [f"{key}={value}" for key, value in sorted(auth_data.items())]
        )

        # Вычисляем secret_key = SHA256(bot_token)
        secret_key = hashlib.sha256(settings.telegram_bot_token.encode()).digest()

        # Вычисляем HMAC-SHA256
        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        # Сравниваем hash
        is_valid = hmac.compare_digest(calculated_hash, received_hash)

        if is_valid:
            logger.info(f"✅ Telegram авторизация валидна для пользователя {auth_data.get('id')}")
        else:
            logger.warning(
                f"⚠️ Невалидная Telegram авторизация для пользователя {auth_data.get('id')}"
            )

        return is_valid

    @staticmethod
    def get_or_create_user(db, auth_data: dict):
        """
        Получить или создать пользователя из данных Telegram Login.

        Args:
            db: Database session
            auth_data: Данные от Telegram (id, first_name, last_name, username, photo_url)

        Returns:
            User: Объект пользователя из БД
        """
        from bot.models import User
        from bot.services.user_service import UserService

        telegram_id = int(auth_data["id"])
        first_name = auth_data.get("first_name", "")
        last_name = auth_data.get("last_name", "")
        username = auth_data.get("username")

        # Полное имя
        full_name = f"{first_name} {last_name}".strip() if last_name else first_name

        user_service = UserService(db)

        # Проверяем существует ли пользователь
        user = user_service.get_user_by_telegram_id(telegram_id)

        if user:
            # Обновляем данные пользователя (могли измениться)
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            if username is not None:
                user.username = username
            db.commit()
            logger.info(f"👤 Обновлён пользователь: {telegram_id} ({full_name})")
        else:
            # Создаем нового пользователя
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"✨ Создан новый пользователь: {telegram_id} ({full_name})")

        return user
