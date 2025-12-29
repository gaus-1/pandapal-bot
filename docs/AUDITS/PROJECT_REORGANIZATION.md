# 📂 План реорганизации проекта PandaPal

**Цель:** Навести порядок, улучшить логику и структуру проекта

---

## 🎯 Проблемы текущей структуры:

1. ❌ **Лишние файлы в корне:** `keep_alive.py`, `webhook_bot.py`, `main.py`
2. ❌ **Пустая папка:** `pandapal-go/src/` (удалить)
3. ❌ **Дублирующиеся документы в корне:** много `.md` файлов
4. ❌ **Неиспользуемые скрипты:** `schedule_knowledge_update.bat`
5. ❌ **Старые миграции:** `analytics_models.py`, `performance_optimization.py` в `alembic/versions/`

---

## ✅ Новая структура проекта:

```
PandaPal/
├── 📁 bot/                          # Backend бот
│   ├── __init__.py
│   ├── config.py                    # Конфигурация
│   ├── database.py                  # База данных
│   ├── models.py                    # SQLAlchemy модели
│   ├── interfaces.py                # Интерфейсы
│   ├── decorators.py                # Декораторы
│   ├── monitoring.py                # Мониторинг
│   │
│   ├── 📁 handlers/                 # Обработчики Telegram
│   │   ├── start.py                 # /start команда
│   │   ├── ai_chat.py               # AI чат
│   │   ├── menu.py                  # Меню
│   │   ├── settings.py              # Настройки
│   │   ├── achievements.py          # Достижения
│   │   ├── location.py              # Геолокация
│   │   ├── parent_dashboard.py      # Родительская панель
│   │   ├── parental_control.py      # Родительский контроль
│   │   └── admin_commands.py        # Админ команды
│   │
│   ├── 📁 keyboards/                # Telegram клавиатуры
│   │   ├── main_kb.py
│   │   └── achievements_kb.py
│   │
│   ├── 📁 services/                 # Бизнес-логика
│   │   ├── ai_response_generator_solid.py  # AI генератор
│   │   ├── ai_service_solid.py             # AI сервис
│   │   ├── simple_ai_service.py            # Простой AI
│   │   ├── ai_context_builder.py           # Контекст AI
│   │   ├── ai_moderator.py                 # AI модератор
│   │   ├── moderation_service.py           # Модерация
│   │   ├── advanced_moderation.py          # Продвинутая модерация
│   │   ├── vision_service.py               # Анализ изображений
│   │   ├── speech_service.py               # Распознавание речи
│   │   ├── token_rotator.py                # Ротация токенов
│   │   ├── user_service.py                 # Пользователи
│   │   ├── history_service.py              # История
│   │   ├── cache_service.py                # Кэширование
│   │   ├── knowledge_service.py            # База знаний
│   │   ├── parental_control.py             # Родительский контроль
│   │   ├── simple_engagement.py            # Вовлеченность
│   │   ├── simple_monitor.py               # Простой мониторинг
│   │   └── web_scraper.py                  # Скрапинг
│   │
│   └── 📁 security/                 # OWASP безопасность
│       ├── crypto.py                # Шифрование
│       ├── headers.py               # HTTP заголовки
│       ├── integrity.py             # Целостность + SSRF
│       └── audit_logger.py          # Аудит логирование
│
├── 📁 frontend/                     # Frontend React
│   ├── src/
│   │   ├── components/              # React компоненты
│   │   ├── game/                    # PandaPal Go игра
│   │   ├── security/                # Безопасность frontend
│   │   ├── monitoring/              # Мониторинг
│   │   ├── hooks/                   # React хуки
│   │   ├── pages/                   # Страницы
│   │   └── utils/                   # Утилиты
│   ├── public/                      # Статика
│   └── package.json
│
├── 📁 tests/                        # Тесты
│   ├── unit/                        # Юнит тесты
│   │   ├── test_config.py
│   │   ├── test_moderation_service.py
│   │   ├── test_security.py
│   │   └── ...
│   ├── integration/                 # Интеграционные
│   │   └── test_ai_solid_integration.py
│   └── conftest.py
│
├── 📁 alembic/                      # Миграции БД
│   ├── versions/
│   │   ├── 0fb5d4bc5f51_initial_database_schema.py
│   │   └── 7e511929fac4_remove_teacher_user_type.py
│   └── env.py
│
├── 📁 scripts/                      # Вспомогательные скрипты
│   ├── analytics_dashboard.py       # Аналитика
│   ├── reset_alembic.py             # Сброс миграций
│   ├── security_check.py            # Проверка безопасности
│   └── test_imports.py              # Проверка импортов
│
├── 📁 docs/                         # Документация
│   ├── 📄 SECURITY/                 # Безопасность
│   │   ├── SECURITY_AUDIT_REPORT.md
│   │   ├── COMPATIBILITY_CHECK.md
│   │   └── SECURITY_GUIDE.md
│   │
│   ├── 📄 SETUP/                    # Настройка
│   │   ├── ANALYTICS_SETUP.md
│   │   ├── VOICE_SETUP.md
│   │   ├── WEBHOOK_SETUP.md
│   │   ├── DOMAIN_SETUP.md
│   │   └── SEO_SETUP_GUIDE.md
│   │
│   ├── 📄 ARCHITECTURE/             # Архитектура
│   │   ├── BOT_FUNCTIONALITY_MAP.md
│   │   ├── CODE_QUALITY_AUDIT.md
│   │   └── ENGAGEMENT_SYSTEM.md
│   │
│   ├── 📄 MARKETING/                # Маркетинг
│   │   ├── SEO_STRATEGY.md
│   │   └── TELEGRAM_BOT_SEO.md
│   │
│   └── 📄 TESTING/                  # Тестирование
│       ├── TESTING.md
│       └── FINAL_TEST_COVERAGE_REPORT.md
│
├── 📁 logs/                         # Логи (в .gitignore)
│
├── 📄 README.md                     # Главный README
├── 📄 README_EN.md                  # English README
├── 📄 CONTRIBUTING.md               # Гайд для контрибуторов
├── 📄 LICENSE                       # Лицензия (добавить)
│
├── ⚙️ .env                          # Переменные окружения
├── ⚙️ .env.template                 # Шаблон .env
├── ⚙️ .gitignore                    # Git исключения
├── ⚙️ requirements.txt              # Python зависимости
├── ⚙️ pyproject.toml                # Python проект
├── ⚙️ pytest.ini                    # Pytest конфиг
├── ⚙️ pyrightconfig.json            # Pyright конфиг
├── ⚙️ alembic.ini                   # Alembic конфиг
├── ⚙️ render.yaml                   # Render деплой
├── ⚙️ docker-compose.yml            # Docker compose
├── ⚙️ Dockerfile                    # Docker backend
└── ⚙️ Aptfile                       # Системные пакеты
```

---

## 🗑️ Файлы на удаление:

### В корне:
- ❌ `keep_alive.py` - не используется
- ❌ `webhook_bot.py` - дубликат функционала
- ❌ `main.py` - точка входа в `bot/__init__.py`
- ❌ `update_knowledge_base.py` - переместить в `scripts/`
- ❌ `schedule_knowledge_update.bat` - Windows скрипт (не нужен)
- ❌ `pandapal-go/` - пустая папка

### В alembic/versions/:
- ❌ `analytics_models.py` - старая миграция
- ❌ `performance_optimization.py` - старая миграция

---

## 📦 Документы на перемещение:

### Из корня в `docs/SECURITY/`:
- `SECURITY_AUDIT_REPORT.md`
- `COMPATIBILITY_CHECK.md`

### Из корня в `docs/SETUP/`:
- `DOMAIN_SETUP.md`

### Из корня в `docs/ARCHITECTURE/`:
- `CODE_QUALITY_AUDIT.md`

---

## ✨ Новые файлы для добавления:

1. **LICENSE** - MIT License
2. **CHANGELOG.md** - История изменений
3. **.github/workflows/** - CI/CD (опционально)
4. **docs/API.md** - API документация

---

## 🔧 План действий:

### Этап 1: Очистка корня ✅
- [x] Удалить неиспользуемые файлы
- [x] Удалить пустые папки

### Этап 2: Реорганизация docs/ ✅
- [x] Создать подпапки по категориям
- [x] Переместить документы

### Этап 3: Очистка alembic/ ✅
- [x] Удалить старые миграции

### Этап 4: Перемещение скриптов ✅
- [x] Переместить в `scripts/`

### Этап 5: Добавление новых файлов ✅
- [x] Создать LICENSE
- [x] Создать CHANGELOG.md

### Этап 6: Обновление README ✅
- [x] Обновить структуру в README
- [x] Добавить badges

---

## 📊 Результат:

### До:
- 🔴 30+ файлов в корне
- 🔴 Неорганизованная документация
- 🔴 Дублирующиеся скрипты

### После:
- ✅ 15 файлов в корне (только конфиги)
- ✅ Структурированная документация
- ✅ Чистые папки по назначению
- ✅ Логичная иерархия

---

**Статус:** 🚀 Готово к выполнению
