"""
Юнит-тесты для модулей безопасности PandaPal Bot.
Тестируют OWASP Top 10 2021 защиту.
"""

import json

import pytest

from bot.security import IntegrityChecker, SSRFProtection, sanitize_input, validate_url_safety
from bot.security.audit_logger import AuditLogger, SecurityEventSeverity, SecurityEventType


@pytest.mark.unit
@pytest.mark.security
class TestIntegrityChecker:
    """Тесты проверки целостности данных."""

    def test_checksum_calculation(self):
        """Тест вычисления контрольной суммы."""
        data = "Test data for checksum"
        checksum = IntegrityChecker.calculate_checksum(data)

        assert checksum is not None
        assert len(checksum) == 64  # SHA-256 = 64 символа в hex

    def test_checksum_verification(self):
        """Тест проверки контрольной суммы."""
        data = "Test data"
        checksum = IntegrityChecker.calculate_checksum(data)

        # Проверяем правильную контрольную сумму
        assert IntegrityChecker.verify_checksum(data, checksum) is True

        # Проверяем неправильную контрольную сумму
        assert IntegrityChecker.verify_checksum(data, "wrong_checksum") is False

    def test_safe_json_loads(self):
        """Тест безопасной десериализации JSON."""
        # Валидный JSON
        valid_json = '{"key": "value", "number": 42}'
        result = IntegrityChecker.safe_json_loads(valid_json)
        assert result == {"key": "value", "number": 42}

        # Невалидный JSON
        invalid_json = '{"key": "value"'
        result = IntegrityChecker.safe_json_loads(invalid_json)
        assert result is None

        # Слишком большой JSON
        large_json = json.dumps({"key": "x" * 2000000})
        result = IntegrityChecker.safe_json_loads(large_json, max_size=1024 * 1024)
        assert result is None

    def test_sanitize_user_input(self):
        """Тест очистки пользовательского ввода."""
        # Нормальный ввод
        normal_input = "Привет, как дела?"
        result = sanitize_input(normal_input)
        assert result == normal_input

        # Ввод с управляющими символами
        malicious_input = "Test\x00\x01\x02"
        result = sanitize_input(malicious_input)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result

        # Слишком длинный ввод
        long_input = "x" * 5000
        result = sanitize_input(long_input, max_length=4000)
        assert len(result) == 4000


@pytest.mark.unit
@pytest.mark.security
class TestSSRFProtection:
    """Тесты защиты от SSRF."""

    def test_safe_url_https_only(self):
        """Тест проверки, что разрешен только HTTPS."""
        # HTTPS должен быть разрешен
        https_url = "https://api.telegram.org/bot"
        assert validate_url_safety(https_url) is True

        # HTTP должен быть заблокирован
        http_url = "http://api.telegram.org/bot"
        assert validate_url_safety(http_url) is False

    def test_safe_url_whitelist(self):
        """Тест проверки белого списка доменов."""
        # Разрешенный домен
        allowed_url = "https://api.telegram.org/test"
        assert validate_url_safety(allowed_url) is True

        # Неразрешенный домен
        blocked_url = "https://evil.com/malicious"
        assert validate_url_safety(blocked_url) is False

    def test_safe_url_ip_blocking(self):
        """Тест блокировки прямых IP адресов."""
        # IP адрес должен быть заблокирован
        ip_url = "https://192.168.1.1/test"
        assert validate_url_safety(ip_url) is False

        # Localhost должен быть заблокирован
        localhost_url = "https://127.0.0.1/test"
        assert validate_url_safety(localhost_url) is False

    def test_validate_external_request(self):
        """Тест валидации внешних запросов."""
        # Безопасный запрос
        assert (
            SSRFProtection.validate_external_request("https://api.telegram.org/test", "GET") is True
        )

        # Небезопасный URL
        assert SSRFProtection.validate_external_request("http://evil.com/test", "GET") is False

        # Небезопасный метод
        assert (
            SSRFProtection.validate_external_request("https://api.telegram.org/test", "DELETE")
            is False
        )


@pytest.mark.unit
@pytest.mark.security
class TestAuditLogger:
    """Тесты безопасного логирования."""

    def test_mask_sensitive_data(self):
        """Тест маскировки чувствительных данных."""
        data = {
            "username": "john_doe",
            "password": "secretpassword123",
            "api_key": "sk-1234567890abcdef",
            "telegram_id": 123456789,
            "message": "Hello world",
        }

        masked = AuditLogger.mask_sensitive_data(data)

        # Проверяем, что чувствительные поля замаскированы
        assert "*" in masked["password"]
        assert "*" in masked["api_key"]
        assert len(masked["password"]) == len(data["password"])

        # Проверяем, что обычные поля не изменены
        assert masked["username"] == data["username"]
        assert masked["message"] == data["message"]

    def test_sanitize_log_message(self):
        """Тест очистки сообщений лога."""
        # Нормальное сообщение
        normal_message = "User logged in successfully"
        result = AuditLogger.sanitize_log_message(normal_message)
        assert result == normal_message

        # Сообщение с управляющими символами
        malicious_message = "Test\x00\x01\x02message"
        result = AuditLogger.sanitize_log_message(malicious_message)
        assert "\x00" not in result
        assert "\x01" not in result

        # Очень длинное сообщение
        long_message = "x" * 2000
        result = AuditLogger.sanitize_log_message(long_message)
        assert len(result) <= 1050  # 1000 + "... (truncated)"

    def test_log_security_event(self):
        """Тест логирования событий безопасности."""
        # Тест не должен вызывать исключений
        try:
            AuditLogger.log_security_event(
                event_type=SecurityEventType.CONTENT_BLOCKED,
                severity=SecurityEventSeverity.WARNING,
                message="Test blocked content",
                user_id=12345,
                metadata={"reason": "profanity"},
            )
            assert True
        except Exception as e:
            pytest.fail(f"Логирование вызвало исключение: {e}")

    def test_log_blocked_content(self):
        """Тест логирования заблокированного контента."""
        # Тест не должен вызывать исключений
        try:
            AuditLogger.log_blocked_content(
                user_id=12345,
                content="Запрещенный контент",
                reason="Обнаружена запрещённая тема",
            )
            assert True
        except Exception as e:
            pytest.fail(f"Логирование заблокированного контента вызвало исключение: {e}")

    def test_log_unauthorized_access(self):
        """Тест логирования несанкционированного доступа."""
        # Тест не должен вызывать исключений
        try:
            AuditLogger.log_unauthorized_access(user_id=12345, resource="/admin", action="read")
            assert True
        except Exception as e:
            pytest.fail(f"Логирование несанкционированного доступа вызвало исключение: {e}")

    def test_log_payment_event(self):
        """Тест логирования событий платежей."""
        # Тест не должен вызывать исключений
        try:
            AuditLogger.log_payment_event(
                event_type=SecurityEventType.PAYMENT_CREATED,
                user_id=12345,
                payment_id="test_payment_123",
                amount=599.0,
                currency="RUB",
                plan_id="month",
                payment_method="yookassa_card",
            )
            assert True
        except Exception as e:
            pytest.fail(f"Логирование платежа вызвало исключение: {e}")

    def test_log_subscription_event(self):
        """Тест логирования событий подписок."""
        # Тест не должен вызывать исключений
        try:
            AuditLogger.log_subscription_event(
                event_type=SecurityEventType.SUBSCRIPTION_ACTIVATED,
                user_id=12345,
                subscription_id=1,
                plan_id="month",
            )
            assert True
        except Exception as e:
            pytest.fail(f"Логирование подписки вызвало исключение: {e}")

    def test_log_user_data_access(self):
        """Тест логирования доступа к данным пользователя."""
        # Тест не должен вызывать исключений
        try:
            # Доступ к своим данным
            AuditLogger.log_user_data_access(
                user_id=12345, accessed_user_id=12345, resource="/profile", action="read"
            )

            # Доступ к чужим данным (должен быть WARNING)
            AuditLogger.log_user_data_access(
                user_id=12345,
                accessed_user_id=67890,
                resource="/profile",
                action="read",
                ip_address="192.168.1.1",
            )
            assert True
        except Exception as e:
            pytest.fail(f"Логирование доступа к данным вызвало исключение: {e}")
