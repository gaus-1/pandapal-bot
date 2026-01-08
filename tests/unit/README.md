# Unit Tests - Модульные тесты

Быстрые изолированные тесты отдельных функций и классов. Тестируем логику без внешних зависимостей.

## Что тестируем

- Отдельные функции и методы
- Логика сервисов (с моками внешних API)
- Валидация данных
- Обработка ошибок
- Граничные случаи

## Структура

Тесты рядом с тестируемым кодом:
- `test_*_service.py` - тесты сервисов
- `test_*_handler.py` - тесты handlers
- `test_models.py` - тесты моделей БД

## Примеры

### Тест функции

```python
def test_calculate_xp():
    from bot.services.gamification_service import calculate_xp

    xp = calculate_xp(level=5, base_xp=100)
    assert xp == 500
```

### Тест с моками

```python
from unittest.mock import Mock, patch

@patch('bot.services.yandex_cloud_service.YandexCloudService')
def test_ai_service(mock_yandex):
    mock_yandex.generate_text_response.return_value = "Test response"

    service = AIService(mock_yandex)
    result = service.generate_response("Hello")

    assert result == "Test response"
```

## Запуск

```bash
# Все unit тесты
pytest tests/unit/ -v

# Конкретный файл
pytest tests/unit/test_gamification_service.py -v
```
