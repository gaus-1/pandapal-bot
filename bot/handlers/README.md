# Handlers - Обработчики команд

Здесь обработчики всех команд и сообщений от пользователей. Когда пользователь пишет боту, срабатывает соответствующий handler.

## Что есть

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

## Как регистрируются

Все роутеры собираются в `bot/handlers/__init__.py`:

```python
from .start import router as start_router
from .ai_chat import router as ai_chat_router

routers = [
    start_router,
    ai_chat_router,
    # ... остальные
]
```

Затем они подключаются к Dispatcher в `web_server.py`.

## Примеры

### Простой обработчик
```python
from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer("Привет! Я PandaPal 🐼")
```

### С модерацией
Все пользовательские сообщения должны проходить модерацию:

```python
from bot.services.moderation_service import ContentModerationService

@router.message(F.text)
async def text_handler(message: Message):
    moderation = ContentModerationService()
    result = await moderation.moderate(message.text, user_age=10)

    if result.is_blocked:
        await message.answer("Сообщение не прошло модерацию")
        return

    # Продолжаем обработку
```

### С работой с БД
```python
from bot.database import get_db
from bot.models import User

@router.message(F.text)
async def handler(message: Message):
    with get_db() as db:
        user = db.query(User).filter_by(
            telegram_id=message.from_user.id
        ).first()

        if not user:
            # Создаем нового пользователя
            user = User(telegram_id=message.from_user.id)
            db.add(user)
            db.commit()

        # Работаем с пользователем
```

## Важные правила

- **Всегда модерация** - любой пользовательский ввод проверяй через модерацию
- **Type hints обязательны** - так проще понять что ожидает функция
- **Логируй важное** - используй logger для важных действий
- **Обрабатывай ошибки** - не падай молча, сообщай пользователю что-то понятное
