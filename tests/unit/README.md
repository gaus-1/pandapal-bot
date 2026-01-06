# Unit Tests - Модульные тесты

Быстрые изолированные тесты отдельных функций и классов.

## Что тестируем

- Отдельные функции и методы
- Логика сервисов (с моками)
- Валидация данных
- Обработка ошибок
- Граничные случаи

## Структура

Тесты рядом с тестируемым кодом:
- `test_*_service.py` - тесты сервисов
- `test_*_handler.py` - тесты handlers
- `test_models.py` - тесты моделей БД

## Паттерны

### Тест функции
```python
def test_calculate_xp():
    from bot.services.gamification_service import calculate_xp

    xp = calculate_xp(level=5, base_xp=100)
    assert xp == 500
```

### Тест с моками
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_ai_service():
    with patch('bot.services.yandex_cloud_service.YandexCloudService') as mock:
        mock.return_value.generate_response = AsyncMock(return_value="Test")

        service = AIService()
        result = await service.generate_response("Hello")

        assert result == "Test"
```

### Тест класса
```python
class TestModerationService:
    def test_basic_moderation(self):
        service = ModerationService()
        result = service.moderate("test message")

        assert result.is_allowed is True

    def test_blocked_content(self):
        service = ModerationService()
        result = service.moderate("bad word")

        assert result.is_blocked is True
```

## Запуск

```bash
# Все unit тесты
pytest tests/unit/ -v

# Конкретный тест
pytest tests/unit/test_moderation_service.py -v

# Быстрые тесты (без async)
pytest tests/unit/ -v -k "not async"
```

## Принципы

- Быстрые (без реальных API/БД)
- Изолированные (не зависят друг от друга)
- Детерминированные (одинаковый результат)
- Покрытие граничных случаев
- Покрытие ошибок
