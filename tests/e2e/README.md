# E2E Tests - End-to-End тесты

Тесты полных пользовательских сценариев от начала до конца. Проверяем как система работает в реальных условиях.

## Что тестируем

- Полные пользовательские потоки
- Интеграция всех компонентов (бот, API, БД, внешние сервисы)
- Работа в реальных условиях
- Обработка ошибок на уровне приложения

## Тесты

- `test_complete_user_journey.py` - полный путь пользователя
- `test_full_user_flow.py` - основные сценарии использования
- `test_error_handling_e2e.py` - обработка ошибок

## Пример

### Полный сценарий

```python
@pytest.mark.asyncio
async def test_user_journey():
    # 1. Регистрация
    user = await create_user(telegram_id=123)

    # 2. Отправка сообщения
    response = await send_message(user.id, "Привет")
    assert response is not None

    # 3. Проверка истории
    history = await get_chat_history(user.id)
    assert len(history) > 0

    # 4. Игра
    game = await create_game(user.id, "tictactoe")
    assert game is not None
```

## Запуск

```bash
# Все E2E тесты
pytest tests/e2e/ -v

# С маркером
pytest tests/e2e/ -v -m e2e
```

## Важно

- Самые медленные тесты - проверяют все компоненты вместе
- Требуют полной настройки окружения
- Проверяют реальное поведение системы
