# Integration Tests - Интеграционные тесты

Тесты, проверяющие работу компонентов вместе с реальными сервисами.

## Что тестируем

- Работа с реальной БД (PostgreSQL)
- Интеграция с Yandex Cloud API (GPT, SpeechKit, Vision)
- Интеграция с YooKassa
- Работа handlers с aiogram
- Полные пользовательские сценарии

## Структура

- `test_*_real.py` - тесты с реальными сервисами
- `conftest_payment.py` - фикстуры для платежей

## Паттерны

### Тест с реальной БД
```python
import pytest
from bot.database import get_db
from bot.models import User

@pytest.mark.asyncio
async def test_user_creation(real_db_session):
    with get_db() as db:
        user = User(telegram_id=123, age=10)
        db.add(user)
        db.commit()

        assert db.query(User).filter_by(telegram_id=123).first() is not None
```

### Тест с AI API
```python
from bot.services.ai_service_solid import YandexAIService

@pytest.mark.asyncio
async def test_ai_response():
    service = YandexAIService()
    response = await service.generate_response("Привет", user_age=10)

    assert response is not None
    assert len(response) > 0
```

### Тест handler
```python
from aiogram import Bot, Dispatcher
from aiogram.types import Message, User

@pytest.mark.asyncio
async def test_start_handler():
    bot = Bot(token="test")
    dp = Dispatcher()

    # Регистрация handler
    # Тест команды /start
```

## Запуск

```bash
# Все интеграционные тесты
pytest tests/integration/ -v

# Конкретный тест
pytest tests/integration/test_ai_chat_real.py -v

# С покрытием
pytest tests/integration/ --cov=bot --cov-report=html
```

## Важно

- Используют реальные сервисы (требуют настройки)
- Медленнее unit тестов
- Требуют переменные окружения для API
- Не должны влиять на production данные
