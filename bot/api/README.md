# API - HTTP Endpoints

HTTP endpoints для Telegram Mini App и внешних интеграций.

## Файлы

- `miniapp_endpoints.py` - API для Mini App (AI chat, голос, изображения, streaming)
- `premium_endpoints.py` - YooKassa webhook, создание платежей
- `auth_endpoints.py` - Telegram Login Widget, сессии для веб-сайта
- `games_endpoints.py` - PandaPalGo API (создание игр, ходы, статистика)
- `premium_features_endpoints.py` - Premium функции API
- `metrics_endpoint.py` - метрики и мониторинг
- `validators.py` - Pydantic валидаторы для запросов

## Регистрация

Endpoints подключаются в `web_server.py`:

```python
from bot.api.miniapp_endpoints import setup_miniapp_routes

setup_miniapp_routes(app)
```

## Примеры

### Простой endpoint

```python
from aiohttp import web
from bot.api.validators import ChatRequest

async def chat_endpoint(request: web.Request) -> web.Response:
    data = await request.json()
    chat_request = ChatRequest(**data)
    result = await process_chat(chat_request.message)
    return web.json_response({"response": result})
```

### С авторизацией

Для Mini App нужна проверка авторизации Telegram:

```python
from bot.security.telegram_auth import verify_telegram_auth

async def protected_endpoint(request: web.Request) -> web.Response:
    auth_data = request.headers.get("X-Telegram-Auth")
    if not verify_telegram_auth(auth_data):
        return web.json_response({"error": "Unauthorized"}, status=401)
    # Продолжаем работу
```

### С работой с БД

```python
from bot.database import get_db
from bot.models import User

async def endpoint(request: web.Request) -> web.Response:
    with get_db() as db:
        users = db.query(User).all()
        return web.json_response({"count": len(users)})
```

## Валидация

Все входные данные валидируем через Pydantic - это защищает от некорректных данных:

```python
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    user_id: int
    age: int | None = None
```

Если данные невалидны, Pydantic выбросит ошибку автоматически.

## Обработка ошибок

Всегда обрабатывай ошибки и возвращай понятные сообщения:

```python
try:
    result = await process_request()
    return web.json_response({"result": result})
except ValueError as e:
    return web.json_response({"error": str(e)}, status=400)
except Exception as e:
    logger.error("Ошибка в endpoint", exc_info=True)
    return web.json_response({"error": "Internal error"}, status=500)
```

## Безопасность

Все endpoints автоматически проходят через security middleware:
- Rate limiting - защита от перегрузки
- Валидация всех входных данных
- CSRF защита
- Telegram auth для Mini App

Не отключай эти проверки без крайней необходимости.
