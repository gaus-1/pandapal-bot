# Integration Tests - Интеграционные тесты

Тесты, которые проверяют работу компонентов вместе с реальными сервисами. Здесь тестируем не отдельные функции, а целые сценарии.

## Что тестируем

- Работа с реальной БД (PostgreSQL) - создание пользователей, сохранение данных
- Интеграция с Yandex Cloud API - реальные запросы к GPT, SpeechKit, Vision
- Интеграция с YooKassa - тестируем платежи (в тестовом режиме)
- Работа handlers с aiogram - как бот реагирует на команды
- Полные пользовательские сценарии - от начала до конца

## Структура

- `test_*_real.py` - тесты с реальными сервисами
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

        # Проверяем что пользователь создан
        found = db.query(User).filter_by(telegram_id=123).first()
        assert found is not None
        assert found.age == 10
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
    # Проверяем что ответ подходит для детей
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

- Используют реальные сервисы - нужны переменные окружения для API
- Медленнее unit тестов - делают реальные запросы
- Не должны влиять на production данные - используй тестовую БД
- Могут быть нестабильными - внешние API могут быть недоступны
