# 🐼 PandaPal - AI-ассистент для обучения детей

<div align="center">

![PandaPal Logo](frontend/public/logo.png)

**Безопасный и умный AI-помощник для школьников 6-18 лет**

[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-19.1-61dafb)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[🤖 Telegram Bot](https://t.me/PandaPalBot) • [🌐 Веб-сайт](https://pandapal.ru) • [📚 Документация](https://pandapal.ru/docs)

[English](README_EN.md) | **Русский**

</div>

---

## 🌟 Что такое PandaPal?

**PandaPal** — это образовательная платформа с искусственным интеллектом, созданная специально для детей и подростков. Мы объединили современные технологии AI, геймификацию и строгие стандарты безопасности, чтобы сделать обучение увлекательным и безопасным.

### 🎯 Ключевые особенности

- 🤖 **AI-помощник на базе Google Gemini 1.5 Flash** - отвечает на вопросы, объясняет сложные темы
- 🛡️ **AI-модерация 24/7** - защита от нецензурной лексики и опасного контента
- 📊 **Родительский контроль** - дашборд с аналитикой прогресса
- 🖼️ **Vision API** - анализ фотографий домашних заданий
- 📚 **Веб-парсинг** - актуальные материалы с образовательных сайтов
- 🎯 **Персонализация** - адаптация под возраст (6-18 лет) и уровень
- 🌐 **Современный веб-интерфейс** - адаптивный дизайн для всех устройств

---

## 🚀 Технологический стек

### Frontend (Веб-сайт)
- **React 19** + **TypeScript** - современный UI
- **Tailwind CSS** - адаптивные стили
- **Zustand** - управление состоянием
- **Vite** - быстрая сборка
- **Web Vitals** - мониторинг производительности

### Backend (Telegram Bot)
- **Python 3.11+** - основной язык
- **aiogram 3.x** - современная библиотека для Telegram Bot API
- **SQLAlchemy 2.0** - ORM для работы с БД
- **Alembic** - миграции БД
- **Google Gemini 1.5 Flash** - AI-движок
- **Redis** - кэширование и сессии
- **PostgreSQL** - основная база данных

### DevOps & Deployment
- **Docker** - контейнеризация
- **Render.com** - хостинг
- **GitHub Actions** - CI/CD
- **Nginx** - веб-сервер

---

## 🏗️ Архитектура проекта

```
PandaPal/
├── bot/                        # Telegram Bot (Python)
│   ├── handlers/               # Обработчики команд
│   ├── services/               # Бизнес-логика
│   ├── keyboards/              # Клавиатуры
│   ├── models.py              # Модели БД
│   └── config.py              # Конфигурация
├── frontend/                   # Веб-сайт (React)
│   ├── src/
│   │   ├── components/         # React компоненты
│   │   ├── pages/             # Страницы
│   │   ├── security/          # Безопасность
│   │   └── utils/             # Утилиты
│   ├── public/                # Статические файлы
│   └── dist/                  # Сборка
├── alembic/                   # Миграции БД
├── docs/                      # Документация
├── tests/                     # Тесты
└── scripts/                   # Утилиты
```

---

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/PandaPal.git
cd PandaPal
```

### 2. Настройка Backend (Telegram Bot)
```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp env.template .env
# Отредактируйте .env файл с вашими токенами

# Применить миграции
alembic upgrade head

# Запуск бота
python main.py
```

### 3. Настройка Frontend (Веб-сайт)
```bash
cd frontend

# Установка зависимостей
npm install

# Запуск в режиме разработки
npm run dev

# Сборка для продакшена
npm run build
```

### 4. Настройка переменных окружения
Создайте файл `.env` в корне проекта:
```env
# Telegram Bot
BOT_TOKEN=your_bot_token_here
WEBHOOK_URL=https://your-domain.com/webhook

# Google AI
GOOGLE_API_KEY=your_google_api_key

# Database
DATABASE_URL=postgresql://user:password@localhost/pandapal

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your_secret_key_here
```

---

## 📊 Мониторинг и аналитика

- **📈 Аналитика использования** - детальная статистика по пользователям
- **🔒 Безопасность** - мониторинг подозрительной активности
- **⚡ Производительность** - Core Web Vitals, время ответа
- **🧪 Тестирование** - 175+ автоматических тестов

---

## 🛡️ Безопасность

- **AI-модерация** - автоматическая фильтрация контента
- **Родительский контроль** - настройки доступа и мониторинг
- **Защита данных** - шифрование и безопасное хранение
- **CSP заголовки** - защита от XSS атак
- **Clickjacking защита** - предотвращение встраивания в вредоносные фреймы

---

## 🎯 Возможности

### Для детей (6-18 лет)
- 💬 **Умный чат** - ответы на вопросы по школьной программе
- 📸 **Анализ фото** - помощь с домашними заданиями через Vision API
- 🎓 **Адаптивное обучение** - персонализированные объяснения
- 🏆 **Система достижений** - мотивация к обучению

### Для родителей
- 📊 **Дашборд прогресса** - отслеживание успехов ребенка
- ⚙️ **Настройки безопасности** - контроль доступа и контента
- 📱 **Уведомления** - отчеты о активности
- 🔍 **История общения** - прозрачность взаимодействия с AI

---

## 🌐 Деплой

### Render.com (Рекомендуется)
1. Подключите GitHub репозиторий
2. Настройте переменные окружения
3. Автоматический деплой при каждом push

### Docker
```bash
# Сборка образа
docker build -t pandapal .

# Запуск контейнера
docker run -p 8000:8000 pandapal
```

---

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие PandaPal!

1. **Fork** репозитория
2. Создайте **feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit** изменения (`git commit -m 'Add amazing feature'`)
4. **Push** в branch (`git push origin feature/amazing-feature`)
5. Откройте **Pull Request**

### Стандарты кода
- **Python**: PEP 8, type hints
- **TypeScript**: ESLint, Prettier
- **Тесты**: покрытие >80%
- **Документация**: обновление при изменениях

---

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

---

## 🆘 Поддержка

- **📧 Email**: support@pandapal.ru
- **💬 Telegram**: [@PandaPalSupport](https://t.me/PandaPalSupport)
- **🐛 Issues**: [GitHub Issues](https://github.com/your-username/PandaPal/issues)
- **📖 Документация**: [pandapal.ru/docs](https://pandapal.ru/docs)

---

<div align="center">

**Сделано с ❤️ для образования детей**

[⬆️ Наверх](#-pandapal---ai-ассистент-для-обучения-детей)

</div>
