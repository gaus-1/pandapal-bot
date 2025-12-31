# 🤝 Вклад в PandaPal

Спасибо за интерес к проекту! Мы рады любому вкладу.

## 📋 Содержание

- [Code of Conduct](#code-of-conduct)
- [Как помочь](#как-помочь)
- [Процесс разработки](#процесс-разработки)
- [Соглашения](#соглашения)
- [Тестирование](#тестирование)
- [Вопросы](#вопросы)

---

## 📜 Code of Conduct

Этот проект придерживается профессиональных стандартов разработки и уважительного общения.

### Наши принципы:
✅ Безопасность детей — наш главный приоритет
✅ Качество кода превыше скорости
✅ Взаимное уважение и помощь
✅ Конструктивная критика
✅ Прозрачность и честность

---

## 💡 Как помочь

### **Типы вклада:**

1. **🐛 Исправление багов** — см. [Issues](https://github.com/gaus-1/pandapal-bot/issues?q=is%3Aissue+is%3Aopen+label%3Abug)
2. **✨ Новые фичи** — предложите или реализуйте
3. **📚 Документация** — улучшите или дополните
4. **🧪 Тесты** — увеличьте покрытие
5. **🎨 UI/UX** — улучшите интерфейс
6. **🌍 Локализация** — добавьте языки

### **Что нужно проекту (Priority):**

- [ ] Увеличение тестового покрытия с 39% до 70%
- [ ] Добавление английского языка
- [ ] Улучшение родительской аналитики
- [ ] Оптимизация производительности AI запросов
- [ ] Мобильное приложение (React Native)

---

## 🔄 Процесс разработки

### **Шаг 1: Fork и клонирование**

```bash
# Fork через GitHub UI
# Затем клонируйте свой fork
git clone https://github.com/YOUR_USERNAME/pandapal-bot.git
cd pandapal-bot

# Добавьте upstream
git remote add upstream https://github.com/gaus-1/pandapal-bot.git
```

### **Шаг 2: Создание ветки**

```bash
# Синхронизируйте с upstream
git fetch upstream
git checkout main
git merge upstream/main

# Создайте feature branch
git checkout -b feature/your-feature-name
# или
git checkout -b fix/bug-description
```

### **Шаг 3: Разработка**

```bash
# Установите зависимости
pip install -r requirements.txt
cd frontend && npm install

# Настройте pre-commit
pre-commit install

# Разрабатывайте и тестируйте
# ...

# Запустите тесты
pytest tests/ -v
```

### **Шаг 4: Commit**

```bash
# Используйте Conventional Commits
git add .
git commit -m "feat: Add amazing feature"

# Примеры:
# feat: Add voice message support
# fix: Resolve database connection issue
# docs: Update installation guide
# test: Add tests for AI service
# refactor: Improve code structure
```

### **Шаг 5: Push и Pull Request**

```bash
# Push в свой fork
git push origin feature/your-feature-name

# Создайте Pull Request через GitHub UI
```

---

## 📐 Соглашения

### **Commits (Conventional Commits)**

Формат: `<type>(<scope>): <description>`

**Types:**
- `feat` — новая функция
- `fix` — исправление бага
- `docs` — изменения в документации
- `style` — форматирование, пробелы
- `refactor` — рефакторинг кода
- `test` — добавление тестов
- `chore` — обновление зависимостей

**Примеры:**
```
feat(bot): Add emergency contacts button
fix(api): Resolve authentication error
docs(readme): Update installation steps
test(services): Add unit tests for AI service
```

### **Python Code Style**

- **PEP 8** — стандарт Python
- **Black** — автоформатирование
- **isort** — сортировка импортов
- **Type hints** — обязательны
- **Docstrings** — Google Style

```python
def example_function(param: str, age: int = 10) -> dict:
    """
    Короткое описание функции.

    Args:
        param: Описание параметра
        age: Возраст пользователя (по умолчанию 10)

    Returns:
        Словарь с результатами

    Raises:
        ValueError: Если param пустой
    """
    if not param:
        raise ValueError("param не может быть пустым")

    return {"result": param, "age": age}
```

### **TypeScript/React Code Style**

- **ESLint** — линтер
- **Prettier** — форматирование
- **Functional Components** — с Hooks
- **TypeScript** — строгая типизация

```typescript
interface UserProps {
  name: string;
  age: number;
}

export const UserCard: React.FC<UserProps> = ({ name, age }) => {
  return (
    <div className="user-card">
      <h2>{name}</h2>
      <p>Возраст: {age}</p>
    </div>
  );
};
```

---

## 🧪 Тестирование

### **Обязательно:**

- ✅ Все новые функции должны иметь тесты
- ✅ Покрытие новых функций ≥ 80%
- ✅ Все тесты должны проходить
- ✅ Никаких `TODO` или `skip` в тестах

### **Типы тестов:**

```bash
# Unit тесты
pytest tests/unit/test_your_feature.py -v

# Integration тесты
pytest tests/integration/test_your_feature.py -v

# Coverage
pytest tests/ --cov=bot --cov-report=html
```

### **Пример теста:**

```python
import pytest
from bot.services.your_service import YourService

class TestYourService:
    @pytest.fixture
    def service(self):
        return YourService()

    def test_basic_functionality(self, service):
        """Тест базовой функциональности"""
        result = service.do_something("input")
        assert result == "expected_output"

    @pytest.mark.asyncio
    async def test_async_functionality(self, service):
        """Тест асинхронной функциональности"""
        result = await service.async_method()
        assert result is not None
```

---

## 📝 Pull Request Guidelines

### **Checklist:**

- [ ] Код соответствует стандартам проекта
- [ ] Все тесты проходят (`pytest tests/ -v`)
- [ ] Покрытие новых функций ≥ 80%
- [ ] Документация обновлена (если нужно)
- [ ] Pre-commit hooks прошли
- [ ] Commit messages следуют Conventional Commits
- [ ] PR описание содержит контекст и примеры

### **Шаблон PR:**

```markdown
## Описание
Краткое описание изменений

## Тип изменений
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Как протестировано
Опишите как вы тестировали изменения

## Checklist
- [ ] Код соответствует стандартам
- [ ] Тесты добавлены и проходят
- [ ] Документация обновлена

## Screenshots (если UI изменения)
```

---

## ❓ Вопросы

### **Где получить помощь:**

- 📧 **Email:** dev@pandapal.ru
- 💬 **Issues:** [GitHub Issues](https://github.com/gaus-1/pandapal-bot/issues)
- 📚 **Docs:** [docs/](docs/)

### **Частые вопросы:**

**Q: Как настроить локальное окружение?**
A: См. [README.md](README.md#установка)

**Q: Где найти задачи для новичков?**
A: Issues с меткой `good first issue`

**Q: Как работать с Yandex Cloud API?**
A: См. [docs/YANDEX_CLOUD_SETUP.md](docs/RAILWAY_SETUP.md)

---

## 🎉 Спасибо!

Ваш вклад делает PandaPal лучше для детей и их родителей! ❤️

---

<div align="center">

**С вопросами и предложениями: [dev@pandapal.ru](mailto:dev@pandapal.ru)**

[⬆ Наверх](#-вклад-в-pandapal)

</div>
