# Security Tests - Тесты безопасности

Тесты для проверки безопасности приложения. Критически важны - защищают детей от опасного контента и атак.

## Что тестируем

- Защита от SQL Injection - нельзя ли через запросы удалить данные
- Защита от XSS - нельзя ли внедрить вредоносный код
- Защита от CSRF - нельзя ли выполнить действия от имени другого пользователя
- Rate limiting - защита от перегрузки
- DDoS protection - защита от атак
- Валидация входных данных - проверяем что некорректные данные отклоняются
- Авторизация и аутентификация - только авторизованные пользователи получают доступ

## Тесты

- `test_sql_injection.py` - защита от SQL инъекций
- `test_api_authorization.py` - проверка авторизации
- `test_api_input_validation.py` - валидация входных данных
- `test_ddos_protection.py` - защита от DDoS
- `test_ddos_slowloris.py` - защита от Slowloris атаки

## Примеры

### Тест SQL Injection
```python
@pytest.mark.asyncio
async def test_sql_injection():
    malicious_input = "'; DROP TABLE users; --"

    # Попытка SQL инъекции должна быть безопасной
    result = await api_endpoint(f"/api/user?name={malicious_input}")

    assert result.status == 200
    # Таблица не должна быть удалена - используем ORM, не сырой SQL
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

- Критически важные тесты - должны проходить всегда
- Проверяют защиту от реальных атак - SQL injection, XSS, CSRF
- Регулярно обновляй тесты - появляются новые типы атак
- Если тест падает - это серьезная проблема безопасности
