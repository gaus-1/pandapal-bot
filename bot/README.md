# Bot - Backend логика

Вся логика Telegram-бота. Обработчики команд, бизнес-логика, API для Mini App и настройки.

## Структура

```
bot/
├── handlers/      # Обработчики команд и сообщений
├── services/      # Бизнес-логика (YandexGPT, платежи, игры, модерация)
├── api/           # HTTP endpoints для Mini App
├── config/        # Настройки, промпты для YandexGPT, паттерны модерации
├── security/      # Middleware, валидация, rate limiting
├── localization/  # Переводы интерфейса (ru, en)
├── monitoring/    # Метрики, логи, ошибки
├── models/        # SQLAlchemy модели БД
└── database.py    # Подключение к PostgreSQL
```

## Компоненты

**Handlers** - реагируют на команды и сообщения пользователей. Когда пользователь пишет `/start` или отправляет фото, срабатывает соответствующий handler.

**Services** — вся логика приложения. Генерация ответов (YandexGPT Pro, streaming), модерация контента (150+ паттернов), платежи (YooKassa продакшн), игры (TicTacToe, Checkers, 2048, Эрудит).

**API** - HTTP endpoints для Mini App. Когда пользователь открывает приложение в Telegram, оно обращается к этим endpoints.

**Security** - защита от атак, валидация данных, ограничение запросов. Критически важно для безопасности детей.

## Работа с БД

Всегда используй context manager для работы с базой:

```python
from bot.database import get_db
from bot.models import User

with get_db() as db:
    user = db.query(User).filter_by(telegram_id=123).first()
    # Работаем с пользователем
```

Не забывай закрывать соединения - context manager делает это автоматически.

## Логирование

Используем loguru для логирования:

```python
from loguru import logger

logger.info("Пользователь отправил сообщение")
logger.error("Ошибка при обработке", exc_info=True)
```

Логи помогают понять что происходит в продакшене, когда что-то идет не так.
