"""
Реальные интеграционные тесты для модуля криптографии
Проверяем шифрование и безопасное хранение данных детей
"""

import os

import pytest

from bot.security.crypto import (
    CryptoService,
    SecureStorage,
    decrypt_data,
    encrypt_data,
    get_crypto_service,
    mask_for_logging,
)


class TestCryptoService:
    """Тесты для сервиса шифрования"""

    def test_encryption_decryption_cycle(self):
        """Тест полного цикла шифрования-расшифрования"""
        service = CryptoService("test_secret_key_123")

        # Тестовые данные
        original_data = "Секретное сообщение ребёнка 🐼"

        # Шифруем
        encrypted = service.encrypt(original_data)
        assert encrypted != original_data
        assert isinstance(encrypted, str)

        # Расшифровываем
        decrypted = service.decrypt(encrypted)
        assert decrypted == original_data

    def test_different_keys_produce_different_ciphertexts(self):
        """Разные ключи создают разные шифртексты"""
        data = "Test data"

        service1 = CryptoService("key1")
        service2 = CryptoService("key2")

        encrypted1 = service1.encrypt(data)
        encrypted2 = service2.encrypt(data)

        assert encrypted1 != encrypted2

    def test_cannot_decrypt_with_wrong_key(self):
        """Нельзя расшифровать с неправильным ключом"""
        service1 = CryptoService("correct_key")
        service2 = CryptoService("wrong_key")

        data = "Secret"
        encrypted = service1.encrypt(data)

        # Попытка расшифровать с другим ключом должна провалиться
        with pytest.raises(Exception):
            service2.decrypt(encrypted)

    def test_encrypt_empty_string(self):
        """Шифрование пустой строки"""
        service = CryptoService("test_key")

        encrypted = service.encrypt("")
        decrypted = service.decrypt(encrypted)

        assert decrypted == ""

    def test_encrypt_unicode_characters(self):
        """Шифрование Unicode символов"""
        service = CryptoService("test_key")

        data = "Привет 🌍 Мир! 你好"
        encrypted = service.encrypt(data)
        decrypted = service.decrypt(encrypted)

        assert decrypted == data

    def test_encrypt_long_text(self):
        """Шифрование длинного текста"""
        service = CryptoService("test_key")

        data = "A" * 10000  # Длинный текст
        encrypted = service.encrypt(data)
        decrypted = service.decrypt(encrypted)

        assert decrypted == data

    def test_hash_data_produces_consistent_hash(self):
        """Хеширование данных создаёт консистентный хеш"""
        service = CryptoService("test_key")

        data = "test_data"
        hash1 = service.hash_data(data)
        hash2 = service.hash_data(data)

        # Без соли хеш должен быть одинаковым
        assert hash1 == hash2

    def test_hash_data_with_salt_produces_different_hash(self):
        """Хеширование с разной солью создаёт разные хеши"""
        service = CryptoService("test_key")

        data = "test_data"
        hash1 = service.hash_data(data, salt="salt1")
        hash2 = service.hash_data(data, salt="salt2")

        assert hash1 != hash2

    def test_hash_data_consistency(self):
        """Хеширование данных консистентно"""
        service = CryptoService("test_key")

        data = "1234567890"
        hash1 = service.hash_data(data)
        hash2 = service.hash_data(data)

        # Хеши должны быть одинаковыми
        assert hash1 == hash2


class TestSecureStorage:
    """Тесты для безопасного хранилища"""

    def test_crypto_service_basic_functionality(self):
        """Базовая функциональность CryptoService"""
        crypto = CryptoService("test_key")

        data = "Sensitive information"
        encrypted = crypto.encrypt(data)
        decrypted = crypto.decrypt(encrypted)

        assert decrypted == data


class TestCryptoIntegration:
    """Интеграционные тесты криптографии"""

    def test_parent_can_safely_store_child_data(self):
        """КРИТИЧНО: Родитель может безопасно хранить данные ребёнка"""
        # Создаём сервис шифрования для родителя
        parent_crypto = CryptoService("parent_secret_key")

        # Чувствительные данные ребёнка
        child_data = {
            "name": "Иван",
            "age": "10",
            "school": "СШ №5",
            "class": "5А",
        }

        # Шифруем каждое поле
        encrypted_data = {}
        for key, value in child_data.items():
            encrypted_data[key] = parent_crypto.encrypt(value)

        # Проверяем что всё зашифровано
        for key, encrypted_value in encrypted_data.items():
            assert encrypted_value != child_data[key]

        # Расшифровываем обратно
        decrypted_data = {}
        for key, encrypted_value in encrypted_data.items():
            decrypted_data[key] = parent_crypto.decrypt(encrypted_value)

        # Данные восстановлены корректно
        assert decrypted_data == child_data

    def test_password_based_child_account_protection(self):
        """КРИТИЧНО: Защита аккаунта ребёнка паролем"""
        crypto = CryptoService("test_key")

        # Родитель устанавливает пароль для защиты профиля
        parent_password = "Secure123!Parent"

        # Хешируем пароль
        password_hash = crypto.hash_data(parent_password, salt="user_salt")

        # Попытка доступа с правильным паролем
        assert crypto.hash_data(parent_password, salt="user_salt") == password_hash

        # Попытка доступа с неправильным паролем
        wrong_attempts = [
            "wrong_password",
            "Secure123",
            "Parent123!",
            "",
        ]

        for wrong_password in wrong_attempts:
            assert crypto.hash_data(wrong_password, salt="user_salt") != password_hash

    def test_crypto_service_with_different_data_types(self):
        """Тест CryptoService с разными типами данных"""
        crypto = CryptoService("test_key")

        # Тестируем разные типы данных
        test_cases = [
            "Simple text",
            "Текст на русском 🐼",
            "123456789",
            "Special chars: !@#$%^&*()",
        ]

        for data in test_cases:
            encrypted = crypto.encrypt(data)
            decrypted = crypto.decrypt(encrypted)
            assert decrypted == data, f"Failed for: {data}"
