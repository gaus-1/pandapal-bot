# Security - Безопасность

Модули безопасности: middleware, валидация, защита от атак.

## Модули

- `middleware.py` - security middleware (CSP, CORS, rate limiting)
- `telegram_auth.py` - валидация Telegram Login Widget (HMAC-SHA256)
- `overload_protection.py` - защита от перегрузки сервера
- `audit_logger.py` - логирование безопасности
- `crypto.py` - криптографические функции
- `headers.py` - security headers
- `integrity.py` - проверка целостности данных

## Middleware

Security middleware регистрируется первым в `web_server.py`:

```python
from bot.security.middleware import setup_security_middleware

setup_security_middleware(app)
```

Обеспечивает:
- CSP headers
- CORS настройки
- Rate limiting
- Security headers (X-Frame-Options, X-Content-Type-Options и т.д.)

## Telegram Auth

Валидация данных от Telegram Login Widget:

```python
from bot.security.telegram_auth import verify_telegram_auth

is_valid = verify_telegram_auth(auth_data, secret_key)
```

## Overload Protection

Защита от DDoS и перегрузки:
- Ограничение количества одновременных запросов
- Блокировка подозрительных IP
- Graceful degradation при перегрузке

## Audit Logging

Логирование важных событий безопасности:
- Попытки обхода модерации
- Подозрительные запросы
- Ошибки авторизации

## Важно

- Все модули безопасности критичны
- Не отключать без крайней необходимости
- Регулярно проверять логи безопасности
- Обновлять зависимости для исправления уязвимостей
