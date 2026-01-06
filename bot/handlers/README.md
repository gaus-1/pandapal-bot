# Handlers - Обработчики команд

Обработчики команд и сообщений для Telegram-бота. Используют aiogram 3.x Routers.

## Структура

Каждый файл - отдельный роутер с обработчиками:

- `start.py` - команда /start, приветствие, главное меню
- `ai_chat.py` - общение с AI, обработка текста, голоса, изображений
- `translate.py` - перевод текста через Yandex Translate
- `games.py` - команды для игр PandaPalGo
- `payment_handler.py` - обработка платежей и Premium
- `feedback.py` - сбор обратной связи через Yandex Forms
- `emergency.py` - экстренные номера (112, 101, 102, 103)
- `achievements.py` - достижения и статистика
- `settings.py` - настройки пользователя
- `menu.py` - навигация по меню

## Регистрация

Все роутеры регистрируются в `bot/handlers/__init__.py`:

```python
from .start import router as start_router
from .ai_chat import router as ai_chat_router

routers = [
    start_router,
    ai_chat_router,
    # ...
]
```

## Паттерны

### Базовый обработчик
```python
from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer("Привет!")
```

### С модерацией
```python
from bot.services.moderation_service import ContentModerationService

@router.message(F.text)
async def text_handler(message: Message):
    moderation = ContentModerationService()
    result = await moderation.moderate(message.text, user_age=10)

    if result.is_blocked:
        await message.answer("Сообщение не прошло модерацию")
        return

    # Обработка сообщения
```

### С БД
```python
from bot.database import get_db
from bot.models import User

@router.message(F.text)
async def handler(message: Message):
    with get_db() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        # Работа с пользователем
```

## Важно

- Все пользовательские сообщения проходят через модерацию
- Используй type hints для всех функций
- Логируй важные действия через logger
- Обрабатывай ошибки gracefully
