# Security - Безопасность

Модули безопасности - защита от атак, валидация данных, ограничение запросов. Критически важно для безопасности детей.

## Файлы

- `middleware.py` - security middleware (CSP, CORS, rate limiting)
- `telegram_auth.py` - валидация Telegram Login Widget (HMAC-SHA256)
- `overload_protection.py` - защита от перегрузки сервера
- `audit_logger.py` - логирование важных событий безопасности
- `crypto.py` - криптографические функции
- `headers.py` - security headers
- `integrity.py` - проверка целостности данных

## Middleware

Security middleware регистрируется первым в `web_server.py`:

```python
from bot.security.middleware import setup_security_middleware

setup_security_middleware(app)
```

Что он делает:
- CSP headers - защита от XSS
- CORS настройки - контроль доступа
- Rate limiting - защита от перегрузки
- Security headers - дополнительные заголовки безопасности

## Telegram Auth

Валидация данных от Telegram Login Widget. Telegram подписывает данные, мы проверяем подпись:

```python
from bot.security.telegram_auth import verify_telegram_auth

is_valid = verify_telegram_auth(auth_data, secret_key)
```

Если подпись неверна - значит данные подделаны, отклоняем запрос.

## Overload Protection

Защита от DDoS и перегрузки:
- Ограничение количества одновременных запросов
- Блокировка подозрительных IP
- Graceful degradation - при перегрузке возвращаем ошибку

## Audit Logging

Логируем важные события безопасности:
- Попытки обхода модерации
- Подозрительные запросы
- Ошибки авторизации

Это помогает отследить атаки и проблемы.

## Важно

- Все модули критичны - не отключай без крайней необходимости
- Регулярно проверяй логи - там могут быть признаки атак
- Обновляй зависимости - в них находят уязвимости
