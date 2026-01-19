"""
Модуль криптографической защиты для PandaPal Bot.
OWASP A02:2021 - Cryptographic Failures

Обеспечивает шифрование чувствительных данных:
- API ключи и токены
- Персональные данные пользователей
- Логи и аудит-записи

Использует Fernet (AES 128) для симметричного шифрования.
"""

import base64
import hashlib

from cryptography.fernet import Fernet
from loguru import logger


class CryptoService:
    """
    Сервис криптографической защиты данных.

    Обеспечивает:
    - Шифрование/дешифрование чувствительных данных
    - Безопасное хранение ключей
    - Хеширование для целостности данных
    """

    def __init__(self, secret_key: str | None = None):
        """
        Инициализация криптосервиса.

        Args:
            secret_key: Секретный ключ для шифрования (str или bytes, если None - генерируется)
        """
        if secret_key is None:
            self.secret_key = self._generate_key()
        elif isinstance(secret_key, bytes):
            self.secret_key = secret_key
        else:
            # Если передан str, конвертируем в bytes через хеш
            key_hash = hashlib.sha256(secret_key.encode("utf-8")).digest()
            # Fernet требует ключ длиной 32 байта (base64 encoded)
            self.secret_key = base64.urlsafe_b64encode(key_hash)
        self.fernet = Fernet(self.secret_key)
        logger.info("🔐 CryptoService инициализирован")

    def _generate_key(self) -> bytes:
        """Генерирует новый ключ шифрования."""
        return Fernet.generate_key()

    def encrypt(self, data: str) -> str:
        """
        Шифрует строку данных.

        Args:
            data: Данные для шифрования

        Returns:
            str: Зашифрованные данные в base64
        """
        if not data:
            return ""

        try:
            encrypted_data = self.fernet.encrypt(data.encode("utf-8"))
            return base64.b64encode(encrypted_data).decode("utf-8")
        except Exception as e:
            logger.error(f"❌ Ошибка шифрования: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """
        Дешифрует данные.

        Args:
            encrypted_data: Зашифрованные данные в base64

        Returns:
            str: Расшифрованные данные
        """
        if not encrypted_data:
            return ""

        try:
            decoded_data = base64.b64decode(encrypted_data.encode("utf-8"))
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode("utf-8")
        except Exception as e:
            logger.error(f"❌ Ошибка дешифрования: {e}")
            raise

    def hash_data(self, data: str, salt: str | None = None) -> str:
        """
        Создает хеш данных с солью для целостности.

        Args:
            data: Данные для хеширования
            salt: Соль для дополнительной защиты

        Returns:
            str: SHA-256 хеш данных
        """
        if salt:
            data = f"{data}{salt}"

        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def verify_hash(self, data: str, hash_value: str, salt: str | None = None) -> bool:
        """
        Проверяет целостность данных по хешу.

        Args:
            data: Исходные данные
            hash_value: Хеш для проверки
            salt: Соль, использованная при создании хеша

        Returns:
            bool: True если хеш совпадает
        """
        expected_hash = self.hash_data(data, salt)
        return expected_hash == hash_value

    def mask_sensitive_data(self, data: str, visible_chars: int = 4) -> str:
        """
        Маскирует чувствительные данные для логирования.

        Args:
            data: Данные для маскировки
            visible_chars: Количество видимых символов с начала

        Returns:
            str: Замаскированные данные
        """
        if not data or len(data) <= visible_chars:
            return "*" * len(data) if data else ""

        return data[:visible_chars] + "*" * (len(data) - visible_chars)


class SecureStorage:
    """
    Безопасное хранение чувствительных данных.

    Обеспечивает шифрование данных перед сохранением в БД
    и дешифрование при чтении.
    """

    def __init__(self, crypto_service: CryptoService):
        """
        Инициализация безопасного хранилища.

        Args:
            crypto_service: Экземпляр CryptoService для шифрования
        """
        self.crypto = crypto_service

    def encrypt_field(self, value: str | None) -> str | None:
        """Шифрует поле перед сохранением в БД."""
        if not value:
            return None
        return self.crypto.encrypt(value)

    def decrypt_field(self, encrypted_value: str | None) -> str | None:
        """Дешифрует поле при чтении из БД."""
        if not encrypted_value:
            return None
        return self.crypto.decrypt(encrypted_value)

    def create_audit_hash(self, data: dict) -> str:
        """
        Создает хеш для аудита целостности данных.

        Args:
            data: Словарь с данными для аудита

        Returns:
            str: Хеш для проверки целостности
        """
        # Сортируем ключи для стабильного хеша
        sorted_data = sorted(data.items())
        data_string = str(sorted_data)
        return self.crypto.hash_data(data_string)


# Глобальный экземпляр криптосервиса
_crypto_service = None


def get_crypto_service() -> CryptoService:
    """
    Получить глобальный экземпляр криптосервиса.

    Returns:
        CryptoService: Глобальный экземпляр
    """
    global _crypto_service
    if _crypto_service is None:
        from bot.config import settings

        # Используем SECRET_KEY из настроек как основу для ключа шифрования
        # CryptoService принимает str и сам конвертирует в bytes
        _crypto_service = CryptoService(settings.secret_key)
    return _crypto_service


def get_secure_storage() -> SecureStorage:
    """
    Получить экземпляр безопасного хранилища.

    Returns:
        SecureStorage: Экземпляр безопасного хранилища
    """
    return SecureStorage(get_crypto_service())


# Утилиты для быстрого доступа
def encrypt_data(data: str) -> str:
    """Быстрое шифрование данных."""
    return get_crypto_service().encrypt(data)


def decrypt_data(encrypted_data: str) -> str:
    """Быстрое дешифрование данных."""
    return get_crypto_service().decrypt(encrypted_data)


def mask_for_logging(data: str, visible_chars: int = 4) -> str:
    """Быстрая маскировка для логирования."""
    return get_crypto_service().mask_sensitive_data(data, visible_chars)
