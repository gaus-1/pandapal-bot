# 🐼 PandaPal Bot

**Безопасный ИИ-друг для детей** - Telegram-бот с искусственным интеллектом, созданный специально для образовательных целей детей 1-9 классов.

## 🎯 О проекте

PandaPal - это умный помощник для детей, который:
- 🤖 Отвечает на вопросы с помощью Google Gemini AI
- 🛡️ Фильтрует контент для безопасности детей
- 📚 Предоставляет образовательные материалы
- 👨‍👩‍👧‍👦 Позволяет родителям контролировать активность
- 🎮 Мотивирует через интерактивные задания

## ✨ Основные возможности

### Для детей:
- 💬 **Умные ответы** - AI понимает детские вопросы и отвечает понятно
- 📖 **Образовательный контент** - материалы по школьным предметам
- 🏆 **Система достижений** - мотивация через прогресс и награды
- 🎨 **Интерактивные задания** - интересные упражнения и головоломки

### Для родителей:
- 👀 **Родительский контроль** - просмотр активности ребенка
- ⚙️ **Настройки безопасности** - гибкая конфигурация фильтров
- 📊 **Аналитика прогресса** - отчеты об успехах и интересах
- ⏰ **Контроль времени** - ограничения использования

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/gaus-1/pandapal-bot.git
cd pandapal-bot
```

### 2. Установка зависимостей
```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Linux/macOS)
source venv/bin/activate

# Установка пакетов
pip install -r requirements.txt
```

### 3. Настройка окружения
Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

Заполните необходимые переменные:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@localhost/pandapal
SECRET_KEY=your_secret_key_here
```

### 4. Настройка базы данных
```bash
# Применение миграций
alembic upgrade head
```

### 5. Запуск бота
```bash
python -m bot.main
```

## 🌐 Веб-интерфейс

Проект включает современный веб-сайт на React + TypeScript:

### Запуск frontend:
```bash
cd frontend
npm install
npm run dev
```

Сайт будет доступен по адресу: `http://localhost:5173`

## 🏗️ Архитектура

### Backend (Python)
- **aiogram 3.x** - Telegram Bot API
- **Google Gemini AI** - обработка естественного языка
- **SQLAlchemy** - ORM для работы с БД
- **PostgreSQL** - основная база данных
- **Redis** - кэширование и сессии
- **Alembic** - миграции БД

### Frontend (React + TypeScript)
- **React 18** - пользовательский интерфейс
- **TypeScript** - типизированный JavaScript
- **Tailwind CSS** - стилизация
- **Vite** - сборка и разработка

### Безопасность
- 🔒 **OWASP Top 10** - соответствие стандартам безопасности
- 🛡️ **Фильтрация контента** - AI-модерация сообщений
- 🔐 **Шифрование данных** - защита персональной информации
- 📝 **Аудит логирование** - отслеживание действий

## 📁 Структура проекта

```
PandaPal/
├── bot/                    # Backend Python
│   ├── handlers/           # Обработчики команд
│   ├── services/           # Бизнес-логика
│   ├── security/           # Модули безопасности
│   ├── database/           # Модели БД
│   └── monitoring/         # Мониторинг и метрики
├── frontend/               # Frontend React
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   ├── pages/          # Страницы
│   │   └── config/         # Конфигурация
├── tests/                  # Тесты
├── docs/                   # Документация
├── scripts/                # Вспомогательные скрипты
└── alembic/               # Миграции БД
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest

# Тесты с покрытием
pytest --cov=bot

# Нагрузочное тестирование
python scripts/load_testing.py --users 20 --duration 60
```

## 📊 Мониторинг

- **Prometheus метрики** - `/metrics` endpoint
- **OpenAPI документация** - `/api-docs`
- **Логирование** - структурированные логи
- **Производительность** - мониторинг времени ответа

## 🔧 Разработка

### Pre-commit хуки
```bash
pre-commit install
```

### Форматирование кода
```bash
# Python
black bot/
isort bot/

# TypeScript
npm run format
```

### Линтеры
```bash
# Python
flake8 bot/
pylint bot/

# TypeScript
npm run lint
```

## 📚 Документация

- [Настройка аналитики](docs/SETUP/ANALYTICS_SETUP.md)
- [Безопасность](docs/SECURITY/SECURITY_GUIDE.md)
- [API документация](docs/api/openapi.yaml)
- [Тестирование](docs/TESTING/TESTING.md)

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE)

## 🆘 Поддержка

- 📧 Email: support@pandapal.ru
- 💬 Telegram: [@PandaPalBot](https://t.me/PandaPalBot)
- 🐛 Issues: [GitHub Issues](https://github.com/gaus-1/pandapal-bot/issues)

---

**Сделано с ❤️ для детей и их родителей**
