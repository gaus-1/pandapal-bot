# Bot - Backend логика

Основной модуль Telegram-бота PandaPal. Содержит обработчики команд, бизнес-логику, API endpoints и конфигурацию.

## Структура

```
bot/
├── handlers/      # Обработчики команд Telegram (start, ai_chat, translate, games)
├── services/       # Бизнес-логика (AI, модерация, платежи, игры)
├── api/           # HTTP endpoints для Mini App и внешних сервисов
├── config/         # Настройки, промпты, паттерны модерации
├── security/       # Middleware, валидация, защита от атак
├── keyboards/      # Клавиатуры для Telegram (inline, reply)
├── localization/   # Локализация (ru, en)
├── monitoring/     # Мониторинг и метрики (Prometheus, Sentry)
├── models.py       # SQLAlchemy модели БД
└── database.py     # Подключение к PostgreSQL, connection pool
```

## Основные компоненты

### Handlers
Обработчики команд и сообщений от пользователей Telegram. Используют aiogram Routers для регистрации.

### Services
Бизнес-логика приложения. Каждый сервис отвечает за свою область:
- AI сервисы (YandexGPT, SpeechKit, Vision)
- Модерация контента
- Платежи (YooKassa)
- Игры (TicTacToe, Checkers, 2048)
- Геймификация (достижения, XP)

### API
HTTP endpoints для Telegram Mini App и интеграций:
- `/api/miniapp/*` - Mini App API
- `/api/premium/*` - Premium подписки
- `/api/games/*` - Игры API
- `/api/auth/*` - Авторизация

### Security
Модули безопасности:
- CSP, CORS headers
- Rate limiting
- Overload protection
- Telegram auth validation

### Keyboards
Клавиатуры для Telegram:
- Inline клавиатуры для меню
- Reply клавиатуры для команд
- Клавиатуры достижений

### Localization
Локализация интерфейса:
- Русский (ru)
- Английский (en)
- JSON файлы с переводами

### Monitoring
Мониторинг и метрики:
- Prometheus метрики
- Sentry для отслеживания ошибок
- Интеграция с системой мониторинга

## Архитектура

Следует принципам SOLID:
- **SRP** - каждый модуль отвечает за одну задачу
- **DIP** - зависимости через интерфейсы
- **OCP** - расширяемость без изменения кода

## Работа с БД

Все операции с БД через context manager:
```python
from bot.database import get_db

with get_db() as db:
    user = db.query(User).filter_by(telegram_id=123).first()
```

## Логирование

Используется loguru:
```python
from loguru import logger

logger.info("User action")
logger.error("Error occurred", exc_info=True)
```
