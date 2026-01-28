"""
Модуль безопасности PandaPal Bot.
OWASP Top 10 2021 Security Implementation

Включает:
- Криптографическую защиту (A02)
- Заголовки безопасности (A05)
- Проверку целостности и защиту от SSRF (A08, A10)
- Безопасное логирование (A09)
"""

from bot.security.audit_logger import (
    AuditLogger,
    SecurityEventSeverity,
    SecurityEventType,
    log_security_event,
    mask_sensitive,
)
from bot.security.crypto import (
    CryptoService,
    SecureStorage,
    decrypt_data,
    encrypt_data,
    get_crypto_service,
    get_secure_storage,
    mask_for_logging,
)
from bot.security.headers import (
    SecurityHeaders,
    get_api_security_headers,
    get_standard_security_headers,
    get_telegram_security_headers,
)
from bot.security.integrity import (
    IntegrityChecker,
    SSRFProtection,
    safe_deserialize_json,
    sanitize_input,
    validate_url_safety,
    verify_data_integrity,
)

__all__ = [
    # Crypto
    "CryptoService",
    "SecureStorage",
    "get_crypto_service",
    "get_secure_storage",
    "encrypt_data",
    "decrypt_data",
    "mask_for_logging",
    # Headers
    "SecurityHeaders",
    "get_standard_security_headers",
    "get_telegram_security_headers",
    "get_api_security_headers",
    # Integrity & SSRF
    "IntegrityChecker",
    "SSRFProtection",
    "verify_data_integrity",
    "safe_deserialize_json",
    "validate_url_safety",
    "sanitize_input",
    # Audit Logging
    "AuditLogger",
    "SecurityEventType",
    "SecurityEventSeverity",
    "log_security_event",
    "mask_sensitive",
]
