# API - HTTP Endpoints

HTTP endpoints для Telegram Mini App и внешних интеграций.

## Структура

- `miniapp_endpoints.py` - API для Mini App (AI chat, голос, изображения)
- `premium_endpoints.py` - YooKassa webhook, создание платежей
- `auth_endpoints.py` - Telegram Login Widget, сессии
- `games_endpoints.py` - PandaPalGo API (создание игр, ходы, статистика)
- `premium_features_endpoints.py` - Premium функции API
- `metrics_endpoint.py` - метрики и мониторинг
- `validators.py` - Pydantic валидаторы для запросов

## Регистрация

Endpoints регистрируются в `web_server.py`:

```python
from bot.api.miniapp_endpoints import setup_miniapp_routes

setup_miniapp_routes(app)
```

## Паттерны

### Базовый endpoint
```python
from aiohttp import web
from bot.api.validators import ChatRequest

async def chat_endpoint(request: web.Request) -> web.Response:
    # Валидация
    data = await request.json()
    chat_request = ChatRequest(**data)

    # Логика
    result = await process_chat(chat_request.message)

    # Ответ
    return web.json_response({"response": result})
```

### С авторизацией
```python
from bot.security.telegram_auth import verify_telegram_auth

async def protected_endpoint(request: web.Request) -> web.Response:
    # Проверка авторизации
    auth_data = request.headers.get("X-Telegram-Auth")
    if not verify_telegram_auth(auth_data):
        return web.json_response({"error": "Unauthorized"}, status=401)

    # Логика
```

### С БД
```python
from bot.database import get_db

async def endpoint(request: web.Request) -> web.Response:
    with get_db() as db:
        # Работа с БД
        result = db.query(User).all()
        return web.json_response({"users": len(result)})
```

## Валидация

Все входные данные валидируются через Pydantic:

```python
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    user_id: int
    age: int | None = None
```

## Обработка ошибок

```python
try:
    result = await process_request()
    return web.json_response({"result": result})
except ValueError as e:
    return web.json_response({"error": str(e)}, status=400)
except Exception as e:
    logger.error("Endpoint error", exc_info=True)
    return web.json_response({"error": "Internal error"}, status=500)
```

## Безопасность

- Все endpoints проходят через security middleware
- Rate limiting на уровне middleware
- Валидация всех входных данных
- CSRF защита для форм
- Telegram auth для Mini App
