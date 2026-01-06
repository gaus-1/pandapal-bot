# Security Tests - Тесты безопасности

Тесты для проверки безопасности приложения.

## Что тестируем

- Защита от SQL Injection
- Защита от XSS
- Защита от CSRF
- Rate limiting
- DDoS protection
- Валидация входных данных
- Авторизация и аутентификация

## Тесты

- `test_sql_injection.py` - защита от SQL инъекций
- `test_api_authorization.py` - проверка авторизации
- `test_api_input_validation.py` - валидация входных данных
- `test_ddos_protection.py` - защита от DDoS
- `test_ddos_slowloris.py` - защита от Slowloris атаки

## Паттерны

### Тест SQL Injection
```python
@pytest.mark.asyncio
async def test_sql_injection():
    malicious_input = "'; DROP TABLE users; --"

    # Попытка SQL инъекции должна быть безопасной
    result = await api_endpoint(f"/api/user?name={malicious_input}")

    assert result.status == 200
    # Таблица не должна быть удалена
```

### Тест Rate Limiting
```python
@pytest.mark.asyncio
async def test_rate_limiting():
    # Отправляем много запросов
    for i in range(100):
        response = await api_request("/api/endpoint")

        if i > 60:  # Лимит 60 req/min
            assert response.status == 429  # Too Many Requests
```

### Тест валидации
```python
def test_input_validation():
    from bot.api.validators import ChatRequest

    # Некорректные данные должны быть отклонены
    with pytest.raises(ValidationError):
        ChatRequest(message="", user_id=-1)
```

## Запуск

```bash
# Все security тесты
pytest tests/security/ -v

# Конкретный тест
pytest tests/security/test_sql_injection.py -v
```

## Важно

- Критически важные тесты
- Должны проходить всегда
- Проверяют защиту от реальных атак
- Регулярно обновлять тесты под новые угрозы
