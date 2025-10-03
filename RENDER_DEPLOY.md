# 🚀 Быстрый деплой на Render.com

## ✅ Что готово

- ✅ Токен Telegram настроен в Environment Variables
- ✅ Код в GitHub: https://github.com/gaus-1/pandapal-bot
- ✅ PostgreSQL БД создана на Render
- ✅ .env.example добавлен в репозиторий

---

## 📋 Шаги для деплоя (5 минут)

### 1️⃣ Обновить Environment Variables

**Откройте:** [Render Dashboard](https://dashboard.render.com/)

**Найдите сервис:** `pandapal-bot` (Web Service)

**Нажмите:** Environment → Edit

**Настройте переменные окружения:**
```env
DATABASE_URL=your_database_url_from_render
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash-exp
AI_TEMPERATURE=0.7
SECRET_KEY=your_secret_key
FORBIDDEN_TOPICS=политика,насилие,оружие,наркотики,экстремизм
CONTENT_FILTER_LEVEL=5
FRONTEND_URL=https://pandapal.ru
LOG_LEVEL=INFO
```

**⚠️ ВАЖНО:** Используйте актуальные значения из Render Dashboard!

**Нажмите:** Save Changes

---

### 2️⃣ Запустить деплой

**В том же сервисе:**
1. Нажмите: **Manual Deploy**
2. Выберите: **Deploy latest commit**
3. Подождите 3-5 минут

**Следите за логами:**
```
[Build] Installing dependencies...
[Build] ✓ 60 packages installed
[Deploy] Starting application...
[Deploy] ✅ Gemini AI инициализирован
[Deploy] 📡 Запуск polling...
[Deploy] ✅ Бот запущен успешно!
```

---

### 3️⃣ Проверить работу

**Откройте Telegram:**
1. Найдите: [@PandaPalBot](https://t.me/PandaPalBot)
2. Отправьте: `/start`
3. Дождитесь ответа

**Ожидаемый результат:**
```
Привет, Вячеслав! 👋

Я — PandaPalAI 🐼, твой личный помощник в учёбе!

Что я умею:
✅ Отвечаю на вопросы по любым школьным предметам
✅ Помогаю решать задачи с подробным объяснением
✅ Объясняю сложные темы простым языком
...
```

---

## 🔍 Troubleshooting

### Проблема: Бот не отвечает

**Решение 1: Проверьте логи на Render**
```
Dashboard → pandapal-bot → Logs
Ищите ошибки с [ERROR] или ❌
```

**Решение 2: Проверьте токен**
```bash
# Локально (используйте ваш токен):
python -c "
import asyncio
from aiogram import Bot
bot = Bot(token='YOUR_TELEGRAM_BOT_TOKEN')
me = asyncio.run(bot.get_me())
print(f'Бот: @{me.username}')
"
```

**Решение 3: Перезапустите сервис**
```
Dashboard → pandapal-bot → Manual Deploy → Clear build cache & deploy
```

---

### Проблема: Database connection failed

**Решение: Проверьте DATABASE_URL**
```
1. Dashboard → PostgreSQL Database → Connection Info
2. Скопируйте External Database URL
3. Обновите в Environment Variables
4. Redeploy
```

---

### Проблема: AI не отвечает (Gemini ошибки)

**Решение: Проверьте GEMINI_API_KEY**
```
1. Откройте: https://aistudio.google.com/apikey
2. Проверьте квоту (Usage)
3. Если закончилась — создайте новый ключ
4. Обновите в Environment Variables
5. Redeploy
```

---

## 📊 Мониторинг

### Метрики на Render:

**CPU / Memory:**
```
Dashboard → pandapal-bot → Metrics
Нормально: CPU < 50%, Memory < 300MB
```

**Логи в реальном времени:**
```
Dashboard → pandapal-bot → Logs
Фильтр: [ERROR] или ❌
```

### Проверка БД:

**Подключение:**
```bash
# Используйте DATABASE_URL из Render Dashboard
psql $DATABASE_URL
```

**Проверка таблиц:**
```sql
-- Количество пользователей
SELECT COUNT(*) FROM users;

-- Последние сообщения
SELECT * FROM chat_history ORDER BY timestamp DESC LIMIT 10;

-- Активные сессии
SELECT * FROM learning_sessions WHERE is_completed = FALSE;
```

---

## ✅ Checklist после деплоя

- [ ] Environment Variables обновлены (новый токен)
- [ ] Manual Deploy выполнен успешно
- [ ] Логи показывают "✅ Бот запущен успешно!"
- [ ] Бот отвечает на `/start` в Telegram
- [ ] AI генерирует ответы (протестируйте вопрос)
- [ ] БД подключена (проверьте через psql)

---

## 🔄 Автоматический деплой (опционально)

**Настройте Auto-Deploy:**
```
Dashboard → pandapal-bot → Settings
Auto-Deploy: Yes
Branch: main
```

**Теперь каждый `git push` → автоматический деплой** 🚀

---

## 🌐 Деплой фронтенда

**Исправлена проблема с деплоем фронтенда!**

**Создайте отдельный сервис для фронтенда:**

1. **New → Static Site**
2. **Repository:** `https://github.com/gaus-1/pandapal-bot`
3. **Branch:** `main`
4. **Root Directory:** `frontend`
5. **Build Command:**
   ```bash
   npm ci && npm run build
   ```
6. **Publish Directory:** `dist`

**⚠️ ВАЖНО:** Фронтенд должен быть отдельным сервисом, НЕ частью основного бота!

**Custom Domain:**
```
Settings → Custom Domain → Add Custom Domain
Domain: pandapal.ru
```

**DNS (REG.RU):**
```
Тип: A
Имя: @
Значение: 216.24.57.1
TTL: 300
```

---

## 📞 Поддержка

- **Render Status:** https://status.render.com/
- **Render Docs:** https://render.com/docs
- **Email:** v81158847@gmail.com

---

<p align="center">
  <b>🎉 PandaPal готов к работе! 🐼</b>
</p>

