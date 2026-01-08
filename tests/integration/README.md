# Integration Tests - Интеграционные тесты

Тесты, которые проверяют работу компонентов вместе с реальными сервисами. Тестируем целые сценарии.

## Что тестируем

- Работа с реальной БД (PostgreSQL)
- Интеграция с Yandex Cloud API (GPT, SpeechKit, Vision)
- Интеграция с YooKassa (в тестовом режиме)
- Работа handlers с aiogram
- Полные пользовательские сценарии

## Структура

- `test_*_real.py` - тесты с реальными сервисами
- `test_foreign_languages_*.py` - тесты обработки иностранных языков
- `conftest_payment.py` - фикстуры для платежей

## Примеры

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

        assert user.telegram_id == 123
```

### Тест AI сервиса

```python
@pytest.mark.asyncio
async def test_ai_response():
    from bot.services.ai_service_solid import get_ai_service

    ai_service = get_ai_service()
    response = await ai_service.generate_response(
        user_message="Что такое фотосинтез?",
        user_age=10
    )

    assert len(response) > 0
    assert "растение" in response.lower() or "фотосинтез" in response.lower()
```

## Запуск

```bash
# Все интеграционные тесты
pytest tests/integration/ -v

# Только тесты с реальным API
pytest tests/integration/test_*_real.py -v
```

## Важно

- Эти тесты требуют реальных API ключей в `.env`
- Они медленнее unit тестов
- Используют реальные ресурсы (Yandex Cloud)
