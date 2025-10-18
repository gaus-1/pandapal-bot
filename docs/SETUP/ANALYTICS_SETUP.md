# 📊 Где смотреть статистику посетителей сайта и бота

## 🌐 АНАЛИТИКА САЙТА

### 1️⃣ **Google Analytics 4** (Бесплатно)

**Что показывает:**
- 👥 Количество посетителей
- 📍 География (страны, города)
- 🕐 Время на сайте
- 📄 Просмотренные страницы
- 📱 Устройства (десктоп/мобильные)
- 🔗 Источники трафика (поиск, прямые заходы, соц. сети)
- 📈 Real-time посетители (кто сейчас на сайте)

**Как настроить:**

1. **Создайте аккаунт:**
   - Зайдите: https://analytics.google.com
   - Войдите под Google аккаунтом
   - Нажмите "Начать измерения"

2. **Создайте ресурс:**
   - Название: "PandaPal"
   - Часовой пояс: Москва (UTC+3)
   - Валюта: RUB (рубли)

3. **Добавьте поток данных:**
   - Выберите "Веб"
   - URL: `https://pandapal.ru`
   - Название потока: "PandaPal Website"

4. **Получите ID измерения:**
   - Формат: `G-XXXXXXXXXX`
   - Скопируйте его

5. **Вставьте в код:**
   - Откройте `frontend/index.html`
   - Найдите строку 157 и 162:
   ```html
   <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
   ```
   - Замените `G-XXXXXXXXXX` на ваш ID (2 места)

6. **Задеплойте сайт**

7. **Проверьте работу:**
   - Через 24-48 часов зайдите в Google Analytics
   - Откройте "Отчеты" → "Реал-тайм"
   - Увидите посетителей в режиме реального времени

**Где смотреть статистику:**
- 🔗 https://analytics.google.com
- Вкладка "Отчеты"
- Раздел "Реал-тайм" - кто сейчас на сайте
- Раздел "Обзор" - общая статистика

---

### 2️⃣ **Яндекс.Метрика** (Бесплатно, для России)

**Что показывает:**
- 👥 Количество посетителей
- 🗺️ Карта кликов (где нажимают)
- 🎬 Вебвизор (записи сессий пользователей)
- 📊 Конверсии и цели
- 🔥 Тепловая карта
- ⚡ Скорость загрузки страниц
- 📱 Детальная аналитика по устройствам

**Как настроить:**

1. **Создайте счетчик:**
   - Зайдите: https://metrika.yandex.ru
   - Войдите под Яндекс ID
   - Нажмите "Добавить счетчик"

2. **Заполните данные:**
   - Адрес сайта: `https://pandapal.ru`
   - Название: "PandaPal"
   - Часовой пояс: Москва

3. **Включите функции:**
   - ✅ Вебвизор (записи сессий)
   - ✅ Карта кликов
   - ✅ Отслеживание хеша
   - ✅ Электронная торговля (если планируете продажи)

4. **Получите номер счетчика:**
   - Формат: 8-значное число, например `12345678`
   - Скопируйте его

5. **Вставьте в код:**
   - Откройте `frontend/index.html`
   - Найдите строку 182 и 191:
   ```html
   ym(XXXXXXXX, "init", {...});
   ```
   - Замените `XXXXXXXX` на ваш номер (2 места)

6. **Задеплойте сайт**

7. **Проверьте установку:**
   - Зайдите в Метрику
   - Нажмите "Проверка счетчика"
   - Должно быть ✅ "Счетчик установлен"

**Где смотреть статистику:**
- 🔗 https://metrika.yandex.ru
- Вкладка "Посетители" - кто приходит
- Вкладка "Вебвизор" - записи сессий (видео как пользователи используют сайт)
- Вкладка "Карты" - тепловая карта кликов

**💡 СОВЕТ:** Вебвизор показывает РЕАЛЬНОЕ видео как пользователи кликают по сайту!

---

### 3️⃣ **Mixpanel** (Бесплатно до 100K событий/мес)

**Для детальной аналитики поведения:**
- 🎯 User journey (путь пользователя)
- 🔄 Конверсионные воронки
- 🧪 A/B тестирование
- 📧 Email/Push уведомления

Настройка: https://mixpanel.com

---

## 🤖 АНАЛИТИКА TELEGRAM БОТА

### 1️⃣ **Встроенная аналитика Telegram** (Бесплатно)

**Что показывает:**
- 👥 Количество пользователей
- 📈 График роста
- 📊 Активность по дням
- 🌍 Языки пользователей

**Как смотреть:**

1. **Откройте @BotFather:**
   - Напишите `/mybots`
   - Выберите `@pandapal_bot`
   - Нажмите "Bot Settings"
   - Выберите "Statistics"

2. **Что увидите:**
   ```
   📊 Статистика за последние 30 дней:

   👥 Всего пользователей: XXXX
   📈 Новых за месяц: +XXX
   💬 Сообщений получено: XXXX
   📤 Сообщений отправлено: XXXX

   График по дням ───────────
   ```

**Ограничения:**
- Только общая статистика
- Нет детальной аналитики
- Нет разбивки по командам

---

### 2️⃣ **База данных PandaPal** (Встроенная)

**Что показывает:**
- 👤 Все пользователи
- 💬 История сообщений
- 📊 Детальная активность
- ⏰ Время использования
- 🎯 Популярные команды

**Как смотреть:**

#### Вариант А: **Через SQL (для разработчиков)**

```sql
-- Подключитесь к PostgreSQL
-- Хост: dpg-d3bvnm37mgec73a3gjbg-a.frankfurt-postgres.render.com
-- База: pandapal_db
-- Пользователь/пароль: из .env

-- Общая статистика
SELECT
    COUNT(*) as total_users,
    COUNT(CASE WHEN is_active THEN 1 END) as active_users,
    COUNT(CASE WHEN user_type = 'child' THEN 1 END) as children,
    COUNT(CASE WHEN user_type = 'parent' THEN 1 END) as parents
FROM users;

-- Пользователи по дням
SELECT
    DATE(created_at) as date,
    COUNT(*) as new_users
FROM users
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 30;

-- Самые активные пользователи
SELECT
    u.first_name,
    u.telegram_id,
    COUNT(ch.id) as message_count
FROM users u
LEFT JOIN chat_history ch ON u.telegram_id = ch.user_telegram_id
GROUP BY u.telegram_id, u.first_name
ORDER BY message_count DESC
LIMIT 20;

-- Активность по часам
SELECT
    EXTRACT(HOUR FROM timestamp) as hour,
    COUNT(*) as messages
FROM chat_history
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY EXTRACT(HOUR FROM timestamp)
ORDER BY hour;

-- Статистика сообщений
SELECT
    COUNT(*) as total_messages,
    COUNT(CASE WHEN message_type = 'user' THEN 1 END) as user_messages,
    COUNT(CASE WHEN message_type = 'ai' THEN 1 END) as ai_messages,
    MIN(timestamp) as first_message,
    MAX(timestamp) as last_message
FROM chat_history;
```

#### Вариант Б: **Админ команды в боте**

Отправьте боту команды:

```
/status - Общая статистика системы
/health - Здоровье сервисов
/ai_status - Статус AI модели
```

---

### 3️⃣ **Botan.io** (Для детальной аналитики ботов)

**Что показывает:**
- 📊 Детальная аналитика событий
- 🎯 Воронки конверсии
- 👥 Сегментация пользователей
- 📈 Retention (возврат пользователей)
- 🔥 Самые популярные команды

**Как настроить:**

1. Зайдите: https://botan.io
2. Зарегистрируйтесь
3. Создайте проект "PandaPal"
4. Получите API ключ
5. Интегрируйте в код бота

**Код интеграции** (в `bot/monitoring.py`):

```python
import botan

botan_token = "YOUR_BOTAN_TOKEN"

def track_event(uid, message, event_name):
    """Отправка события в Botan"""
    botan.track(botan_token, uid, message, event_name)

# Использование:
track_event(user_id, message, "button_click")
track_event(user_id, message, "ai_question_asked")
track_event(user_id, message, "homework_help_requested")
```

---

### 4️⃣ **Простой дашборд для БД** (Создать самостоятельно)

**Вариант А: pgAdmin** (Графический интерфейс для PostgreSQL)

1. Скачайте: https://www.pgadmin.org/download/
2. Установите
3. Подключитесь к БД Render:
   - Host: `dpg-d3bvnm37mgec73a3gjbg-a.frankfurt-postgres.render.com`
   - Port: `5432`
   - Database: `pandapal_db`
   - Username/Password: из `.env`

4. Создайте SQL запросы для отчетов

**Вариант Б: Google Data Studio** (Бесплатные дашборды)

1. Зайдите: https://datastudio.google.com
2. Создайте отчет
3. Подключите PostgreSQL как источник
4. Создайте визуализации:
   - График роста пользователей
   - Активность по дням
   - Топ пользователей
   - География

---

## 📊 ГОТОВЫЕ ДАШБОРДЫ В БОТЕ

### Админ команды (уже реализованы):

```bash
# Отправьте эти команды в бота @pandapal_bot

/status
# Показывает:
# • Количество пользователей
# • Сообщений сегодня
# • Загрузка CPU/RAM
# • Статус сервисов

/health
# Показывает:
# • Здоровье БД
# • Статус AI
# • Общее состояние системы

/ai_status
# Показывает:
# • Текущая модель AI
# • Температура и параметры
# • Статус доступности
```

---

## 📈 СОЗДАНИЕ СОБСТВЕННОГО ДАШБОРДА

### Вариант 1: Простой Python скрипт

Создайте файл `scripts/analytics_dashboard.py`:

```python
"""
Простой дашборд для просмотра статистики PandaPal
"""

import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Подключение к БД
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def get_stats():
    """Получение основной статистики"""
    with engine.connect() as conn:
        # Общая статистика
        total_users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        active_users = conn.execute(
            text("SELECT COUNT(*) FROM users WHERE is_active = true")
        ).scalar()
        total_messages = conn.execute(text("SELECT COUNT(*) FROM chat_history")).scalar()

        # Сегодняшняя статистика
        today = datetime.now().date()
        messages_today = conn.execute(
            text("SELECT COUNT(*) FROM chat_history WHERE DATE(timestamp) = :today"),
            {"today": today}
        ).scalar()

        # Новые пользователи за неделю
        week_ago = datetime.now() - timedelta(days=7)
        new_users_week = conn.execute(
            text("SELECT COUNT(*) FROM users WHERE created_at >= :week_ago"),
            {"week_ago": week_ago}
        ).scalar()

        print("=" * 60)
        print("📊 СТАТИСТИКА PANDAPAL")
        print("=" * 60)
        print(f"\n👥 ПОЛЬЗОВАТЕЛИ:")
        print(f"   Всего: {total_users}")
        print(f"   Активных: {active_users}")
        print(f"   Новых за неделю: {new_users_week}")

        print(f"\n💬 СООБЩЕНИЯ:")
        print(f"   Всего: {total_messages}")
        print(f"   Сегодня: {messages_today}")

        # Топ-10 активных пользователей
        result = conn.execute(text("""
            SELECT
                u.first_name,
                u.telegram_id,
                COUNT(ch.id) as msg_count
            FROM users u
            LEFT JOIN chat_history ch ON u.telegram_id = ch.user_telegram_id
            GROUP BY u.telegram_id, u.first_name
            ORDER BY msg_count DESC
            LIMIT 10
        """))

        print(f"\n🏆 ТОП-10 АКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ:")
        for i, row in enumerate(result, 1):
            print(f"   {i}. {row[0]} (@{row[1]}): {row[2]} сообщений")

        print("\n" + "=" * 60)

if __name__ == "__main__":
    get_stats()
```

**Использование:**
```bash
python scripts/analytics_dashboard.py
```

---

### Вариант 2: Веб-дашборд (Flask)

Создайте `scripts/web_dashboard.py`:

```python
"""
Веб-дашборд для просмотра статистики в браузере
Запуск: python scripts/web_dashboard.py
Открыть: http://localhost:5000
"""

from flask import Flask, render_template_string
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
engine = create_engine(os.getenv("DATABASE_URL"))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PandaPal Analytics</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        h1 {
            color: #4F46E5;
            text-align: center;
            margin-bottom: 30px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 15px;
            color: white;
            text-align: center;
        }
        .stat-value {
            font-size: 48px;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-label {
            font-size: 16px;
            opacity: 0.9;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #4F46E5;
            color: white;
            font-weight: bold;
        }
        tr:hover {
            background: #f5f5f5;
        }
    </style>
    <meta http-equiv="refresh" content="30">
</head>
<body>
    <div class="container">
        <h1>📊 PandaPal Analytics Dashboard</h1>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Всего пользователей</div>
                <div class="stat-value">{{ total_users }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Активных</div>
                <div class="stat-value">{{ active_users }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Сообщений всего</div>
                <div class="stat-value">{{ total_messages }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Сегодня</div>
                <div class="stat-value">{{ messages_today }}</div>
            </div>
        </div>

        <h2>🏆 Топ-20 активных пользователей</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Имя</th>
                    <th>Telegram ID</th>
                    <th>Сообщений</th>
                    <th>Тип</th>
                </tr>
            </thead>
            <tbody>
                {% for user in top_users %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td>{{ user[0] }}</td>
                    <td>{{ user[1] }}</td>
                    <td>{{ user[2] }}</td>
                    <td>{{ user[3] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <p style="text-align: center; color: #999; margin-top: 30px;">
            Обновляется каждые 30 секунд
        </p>
    </div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    """Главная страница дашборда"""
    with engine.connect() as conn:
        # Получаем статистику
        total_users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        active_users = conn.execute(
            text("SELECT COUNT(*) FROM users WHERE is_active = true")
        ).scalar()
        total_messages = conn.execute(text("SELECT COUNT(*) FROM chat_history")).scalar()

        from datetime import datetime
        today = datetime.now().date()
        messages_today = conn.execute(
            text("SELECT COUNT(*) FROM chat_history WHERE DATE(timestamp) = :today"),
            {"today": today}
        ).scalar() or 0

        # Топ пользователей
        top_users_result = conn.execute(text("""
            SELECT
                u.first_name,
                u.telegram_id,
                COUNT(ch.id) as msg_count,
                u.user_type
            FROM users u
            LEFT JOIN chat_history ch ON u.telegram_id = ch.user_telegram_id
            GROUP BY u.telegram_id, u.first_name, u.user_type
            ORDER BY msg_count DESC
            LIMIT 20
        """))
        top_users = list(top_users_result)

    return render_template_string(
        HTML_TEMPLATE,
        total_users=total_users,
        active_users=active_users,
        total_messages=total_messages,
        messages_today=messages_today,
        top_users=top_users
    )

if __name__ == "__main__":
    print("🚀 Запуск дашборда на http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
```

**Использование:**
```bash
# Установите Flask
pip install flask

# Запустите дашборд
python scripts/web_dashboard.py

# Откройте браузер
http://localhost:5000
```

---

### 3️⃣ **Metabase** (Бесплатный BI инструмент)

**Профессиональные дашборды без кода:**

1. Скачайте: https://www.metabase.com/start/oss/
2. Запустите Metabase
3. Подключите PostgreSQL базу PandaPal
4. Создайте визуализации drag-and-drop

**Примеры графиков:**
- 📈 Рост пользователей по дням
- 🔥 Тепловая карта активности
- 🌍 География пользователей
- 🎯 Конверсия Free → Premium

---

## 🎯 ЧТО ОТСЛЕЖИВАТЬ

### Ключевые метрики:

#### **Для сайта:**
- 👥 Уникальные посетители/день
- 🔗 CTR (клики на "Начать в Telegram")
- ⏱️ Среднее время на сайте (цель: > 2 мин)
- 📉 Показатель отказов (цель: < 50%)
- 📄 Глубина просмотра (цель: > 2 страницы)

#### **Для бота:**
- 📈 Новые пользователи/день
- 💬 Среднее сообщений на пользователя (цель: > 10)
- 🔄 Retention (возврат через 7 дней, цель: > 30%)
- ⭐ Конверсия Free → Premium (цель: > 5%)
- 🎯 Engagement rate (активные/всего, цель: > 40%)

---

## 📱 МОБИЛЬНОЕ ПРИЛОЖЕНИЕ ДЛЯ АНАЛИТИКИ

### Google Analytics App (iOS/Android)

- Скачайте приложение "Google Analytics"
- Войдите под вашим Google аккаунтом
- Выберите ресурс "PandaPal"
- Смотрите статистику в реальном времени на телефоне

### Яндекс.Метрика App (iOS/Android)

- Скачайте "Яндекс.Метрика"
- Войдите под Яндекс ID
- Выберите счетчик "PandaPal"
- Получайте push-уведомления о всплесках трафика

---

## 🚨 НАСТРОЙКА АЛЕРТОВ

### Google Analytics:

1. Зайдите в GA4
2. "Администратор" → "Пользовательские оповещения"
3. Создайте алерт:
   - Название: "Резкий рост трафика"
   - Условие: Пользователи > 1000 за день
   - Email уведомление

### Яндекс.Метрика:

1. Зайдите в Метрику
2. "Настройки" → "Уведомления"
3. Создайте уведомление:
   - Падение трафика > 50%
   - Рост отказов > 70%
   - Email/Telegram уведомление

---

## 📊 ПРИМЕРЫ ОТЧЕТОВ

### Ежедневный отчет (автоматизация):

```python
# scripts/daily_report.py
"""Отправка ежедневного отчета в Telegram"""

import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from telegram import Bot
import asyncio

async def send_daily_report():
    """Отправка ежедневной статистики"""
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    admin_id = 963126718  # Ваш Telegram ID

    # Получаем статистику
    engine = create_engine(os.getenv("DATABASE_URL"))
    with engine.connect() as conn:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        new_users_today = conn.execute(
            text("SELECT COUNT(*) FROM users WHERE DATE(created_at) = :today"),
            {"today": today}
        ).scalar()

        messages_today = conn.execute(
            text("SELECT COUNT(*) FROM chat_history WHERE DATE(timestamp) = :today"),
            {"today": today}
        ).scalar()

        total_users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()

    # Формируем отчет
    report = f"""
📊 <b>Ежедневный отчет PandaPal</b>
📅 {today.strftime('%d.%m.%Y')}

👥 <b>Пользователи:</b>
• Новых за сегодня: {new_users_today}
• Всего: {total_users}

💬 <b>Активность:</b>
• Сообщений сегодня: {messages_today}

🔗 <b>Ссылки:</b>
• Сайт: https://pandapal.ru
• Бот: @pandapal_bot
• Render: https://dashboard.render.com

#отчет #статистика
"""

    await bot.send_message(admin_id, report, parse_mode="HTML")
    print(f"✅ Отчет за {today} отправлен")

if __name__ == "__main__":
    asyncio.run(send_daily_report())
```

**Автоматизация (cron на Render):**
```bash
# Добавьте в Render Cron Job:
# Запуск каждый день в 9:00 утра
0 9 * * * python scripts/daily_report.py
```

---

## 🔐 БЕЗОПАСНОСТЬ ДАННЫХ

### Важно:
- 🔒 Не публикуйте дашборды открыто
- 🔑 Используйте авторизацию для доступа
- 📊 Анонимизируйте данные пользователей
- 🛡️ Соблюдайте GDPR/152-ФЗ

---

## ✅ БЫСТРЫЙ СТАРТ

### Минимальная настройка (5 минут):

1. **Google Analytics:**
   - Создайте аккаунт: https://analytics.google.com
   - Получите ID: `G-XXXXXXXXXX`
   - Вставьте в `frontend/index.html` (строки 157, 162)
   - Задеплойте сайт

2. **Яндекс.Метрика:**
   - Создайте счетчик: https://metrika.yandex.ru
   - Получите номер: `12345678`
   - Вставьте в `frontend/index.html` (строки 182, 191)
   - Задеплойте сайт

3. **Telegram Analytics:**
   - Откройте @BotFather
   - `/mybots` → выберите бота → "Statistics"
   - Готово! Статистика доступна

4. **SQL запросы:**
   - Подключитесь к БД через psql или pgAdmin
   - Используйте готовые SQL запросы выше
   - Сохраните в закладки

---

## 📞 ПОДДЕРЖКА

Если нужна помощь с настройкой:
- 📧 Email: support@pandapal.ru
- 💬 Telegram: @pandapal_support

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

### Документация:
- Google Analytics: https://support.google.com/analytics
- Яндекс.Метрика: https://yandex.ru/support/metrica
- Telegram Bot Analytics: https://core.telegram.org/bots/api#getting-updates

### Курсы:
- Google Analytics Academy (бесплатно)
- Яндекс.Практикум - Аналитика данных
- DataCamp - Data Analysis

---

**Начните отслеживать ваших пользователей уже сегодня! 📊🚀**

*Документ обновлен: 2025-10-08*
