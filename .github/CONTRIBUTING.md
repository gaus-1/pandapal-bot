# Contributing to PandaPal

Спасибо за интерес к проекту! Мы ценим любой вклад в развитие образовательной платформы.

## Содержание

- [Кодекс поведения](#кодекс-поведения)
- [Как внести вклад](#как-внести-вклад)
- [Процесс разработки](#процесс-разработки)
- [Стандарты кода](#стандарты-кода)
- [Тестирование](#тестирование)
- [Коммиты и Pull Requests](#коммиты-и-pull-requests)

## Кодекс поведения

Этот проект следует [Кодексу поведения](CODE_OF_CONDUCT.md). Участвуя в проекте, вы соглашаетесь соблюдать его условия.

## Как внести вклад

### Сообщить об ошибке

1. Проверьте, что ошибка еще не была [зарегистрирована](https://github.com/gaus-1/pandapal-bot/issues)
2. Создайте новый issue, используя шаблон "Bug Report"
3. Опишите проблему максимально подробно:
   - Шаги для воспроизведения
   - Ожидаемое поведение
   - Фактическое поведение
   - Скриншоты (если применимо)
   - Версия Python, Node.js, браузера

### Предложить новую функцию

1. Создайте issue с шаблоном "Feature Request"
2. Опишите:
   - Проблему, которую решает функция
   - Предлагаемое решение
   - Альтернативные варианты
   - Влияние на существующую функциональность

### Внести код

1. **Fork** репозитория
2. Создайте ветку от `main`:
   ```bash
   git checkout -b feature/your-feature-name
   # или
   git checkout -b fix/your-bug-fix
   ```
3. Внесите изменения
4. Запустите тесты и линтеры
5. Создайте Pull Request

## Процесс разработки

### Настройка окружения

```bash
# Клонирование
git clone https://github.com/gaus-1/pandapal-bot.git
cd pandapal-bot

# Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install

# Pre-commit hooks
pip install pre-commit
pre-commit install
```

### Структура проекта

```
PandaPal/
├── bot/           # Backend (Python, aiogram)
├── frontend/      # Frontend (React, TypeScript)
├── tests/         # Тесты
├── docs/          # Документация
└── scripts/       # Утилиты
```

## Стандарты кода

### Python (Backend)

- **Стиль**: Black (line-length=100)
- **Импорты**: isort (profile="black")
- **Линтеры**: ruff, pylint
- **Type hints**: обязательны для публичных функций
- **Docstrings**: Google style для публичных API

```python
def calculate_score(user_id: int, points: int) -> int:
    """
    Подсчитать общий счет пользователя.

    Args:
        user_id: ID пользователя
        points: Количество очков для добавления

    Returns:
        Обновленный общий счет

    Raises:
        ValueError: Если points отрицательное
    """
    if points < 0:
        raise ValueError("Points must be non-negative")
    # ...
```

### TypeScript (Frontend)

- **Стиль**: Prettier
- **Линтер**: ESLint
- **Типы**: строгая типизация, избегать `any`
- **Компоненты**: функциональные компоненты с хуками

```typescript
interface UserProfileProps {
  userId: number;
  onUpdate?: (profile: UserProfile) => void;
}

export function UserProfile({ userId, onUpdate }: UserProfileProps) {
  // ...
}
```

### Общие правила

- **Комментарии**: на русском языке
- **Коммиты**: на английском языке
- **Именование**:
  - Python: `snake_case`
  - TypeScript: `camelCase` для переменных, `PascalCase` для компонентов
- **Файлы**: максимум 500 строк (разбивать на модули)

## Тестирование

### Запуск тестов

```bash
# Backend
pytest tests/ -v
pytest tests/ --cov=bot --cov-report=html

# Frontend
cd frontend
npm test
npm run test:e2e
```

### Требования к тестам

- **Unit тесты**: для всех новых функций
- **Integration тесты**: для API endpoints
- **E2E тесты**: для критических пользовательских сценариев
- **Покрытие**: минимум 80% для новых файлов

### Пример теста

```python
def test_calculate_score():
    """Тест подсчета очков."""
    result = calculate_score(user_id=1, points=100)
    assert result == 100

    with pytest.raises(ValueError):
        calculate_score(user_id=1, points=-10)
```

## Коммиты и Pull Requests

### Формат коммитов (Conventional Commits)

```
<type>: <description>

[optional body]

[optional footer]
```

**Типы:**
- `feat:` — новая функция
- `fix:` — исправление бага
- `refactor:` — рефакторинг без изменения функциональности
- `docs:` — изменения в документации
- `test:` — добавление или изменение тестов
- `chore:` — изменения в сборке, зависимостях
- `style:` — форматирование кода
- `perf:` — оптимизация производительности
- `security:` — исправления безопасности

**Примеры:**
```bash
feat: add voice message support for AI chat
fix: handle empty message validation in chat handler
refactor: split ai_chat.py into modular structure
docs: update API documentation for streaming endpoints
test: add e2e tests for homework checking feature
```

### Pull Request

1. **Название**: следует формату коммитов
2. **Описание**: используйте шаблон PR
3. **Checklist**:
   - [ ] Код соответствует стандартам проекта
   - [ ] Добавлены/обновлены тесты
   - [ ] Все тесты проходят
   - [ ] Обновлена документация
   - [ ] Нет конфликтов с `main`
   - [ ] Pre-commit hooks проходят

4. **Review**: минимум 1 одобрение перед merge

### Процесс Review

- Отвечайте на комментарии конструктивно
- Вносите правки в ту же ветку
- После одобрения PR будет смержен через squash merge

## Безопасность

- **НЕ коммитьте** секреты, токены, API ключи
- Используйте `.env` для локальных секретов
- Сообщайте об уязвимостях через [Security Policy](SECURITY.md)

## Дополнительные ресурсы

- [Архитектура проекта](../docs/architecture/)
- [API документация](../docs/api/)
- [Руководство по тестированию](../docs/development/testing.md)

## Вопросы

Если у вас есть вопросы:
1. Проверьте [документацию](../docs/)
2. Поищите в [Issues](https://github.com/gaus-1/pandapal-bot/issues)
3. Создайте новый Issue с вопросом

---

Спасибо за ваш вклад в PandaPal!
