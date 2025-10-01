# 🚀 Инструкция по деплою PandaPal

## ✅ Что уже готово

- ✅ Backend полностью реализован (Python + aiogram + Gemini AI)
- ✅ Frontend собран и готов (React + TypeScript + Tailwind)
- ✅ База данных инициализирована (PostgreSQL на Render)
- ✅ .env конфигурация настроена
- ✅ requirements.txt обновлён
- ✅ README.md создан (300+ строк документации)
- ✅ .gitignore добавлен
- ✅ Коммит создан локально

---

## 📋 Что нужно сделать для запуска

### 1️⃣ Git Push в GitHub

**Проблема:** Требуется авторизация с Personal Access Token

**Решение:**

```bash
# Используйте ваш токен PAT (ghp_...)
git push -u origin main
# При запросе пароля введите ваш Personal Access Token
```

**Альтернатива (если токен не работает):**

```bash
# Настройка credential helper
git config --global credential.helper wincred

# Или используйте SSH вместо HTTPS
git remote set-url origin git@github.com:gaus-1/pandapal-bot.git
git push -u origin main
```

---

### 2️⃣ Деплой бота на Render.com

#### A. Обновить существующий Web Service

1. Откройте **Render Dashboard**
2. Найдите сервис `pandapal-bot`
3. Нажмите **Manual Deploy** → **Deploy latest commit**
4. Дождитесь успешного деплоя (3-5 минут)

#### B. Или создать новый Web Service

1. **New → Web Service**
2. **Repository:** `https://github.com/gaus-1/pandapal-bot`
3. **Branch:** `main`
4. **Root Directory:** `./` (или оставить пустым)
5. **Build Command:**
   ```bash
   pip install -r requirements.txt
   ```
6. **Start Command:**
   ```bash
   python main.py
   ```
7. **Environment Variables** (добавьте все из `.env`):
   ```env
   DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname
   TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash-exp
   AI_TEMPERATURE=0.7
   SECRET_KEY=pandapal_secret_key_2025_production
   FORBIDDEN_TOPICS=политика,насилие,оружие,наркотики,экстремизм
   CONTENT_FILTER_LEVEL=5
   FRONTEND_URL=https://pandapal.ru
   ```

---

### 3️⃣ Деплой фронтенда на Render

#### Вариант 1: Static Site (рекомендуется)

1. **New → Static Site**
2. **Repository:** `https://github.com/gaus-1/pandapal-bot`
3. **Branch:** `main`
4. **Root Directory:** `frontend`
5. **Build Command:**
   ```bash
   npm install && npm run build
   ```
6. **Publish Directory:** `dist`
7. **Custom Domain:** `pandapal.ru`

#### Вариант 2: Web Service с serve

Если Static Site не работает с A-record:

1. **Build Command:**
   ```bash
   cd frontend && npm install && npm run build
   ```
2. **Start Command:**
   ```bash
   cd frontend && npx serve -s dist -l $PORT
   ```

---

### 4️⃣ Настройка DNS (REG.RU)

**Для `pandapal.ru`:**

```
Тип: A
Имя: @
Значение: 216.24.57.1
TTL: 300
```

**Для `www.pandapal.ru`:**

```
Тип: A
Имя: www
Значение: 216.24.57.1
TTL: 300
```

⚠️ **Важно:** REG.RU автоматически добавляет суффикс домена к CNAME записям. Используйте A-записи!

---

### 5️⃣ Проверка работы

#### Бот:

1. Откройте https://t.me/PandaPalBot
2. Отправьте `/start`
3. Проверьте ответ AI

#### Фронтенд:

1. Откройте https://pandapal.ru
2. Проверьте адаптивность (F12 → Device Toolbar)
3. Проверьте QR-код и кнопку Telegram

#### База данных:

```bash
# Подключитесь к PostgreSQL
psql postgresql://pandapal_user:7rCuhY8R8C1fHvblUPdFjLzgMoLKn95D@dpg-d3bvnm37mgec73a3gjbg-a.frankfurt-postgres.render.com/pandapal_db

# Проверьте таблицы
\dt

# Проверьте пользователей
SELECT * FROM users LIMIT 5;
```

---

### 6️⃣ Мониторинг и отладка

#### Логи на Render:

1. Dashboard → Web Service → Logs
2. Смотрите реальные логи в реальном времени

#### Локальные логи:

```bash
# Логи хранятся в папке logs/
tail -f logs/pandapal_2025-10-01.log
```

#### Проверка здоровья бота:

```python
# Запустите локально
python -c "
from bot.database import DatabaseService
from bot.services.ai_service import GeminiAIService

print('✅ БД:', DatabaseService.check_connection())
ai = GeminiAIService()
print('✅ AI:', ai.get_model_info())
"
```

---

## 🔧 Troubleshooting

### Проблема: "ModuleNotFoundError: No module named 'aiogram'"

**Решение:**
```bash
pip install -r requirements.txt
```

### Проблема: "DATABASE_URL field required"

**Решение:**
- Проверьте, что `.env` файл без UTF-8 BOM
- Убедитесь, что все переменные lowercase (database_url, не DATABASE_URL)

### Проблема: Git push требует пароль

**Решение:**
```bash
# Используйте Personal Access Token вместо пароля
# Создайте токен: GitHub → Settings → Developer settings → Personal access tokens
# Scope: repo (полный доступ)
```

### Проблема: Render не может собрать фронтенд

**Решение:**
```bash
# Убедитесь, что в frontend/package.json есть:
"scripts": {
  "build": "tsc -b && vite build"
}
```

---

## 📞 Поддержка

- **Email:** v81158847@gmail.com
- **Telegram:** @PandaPalBot
- **GitHub Issues:** https://github.com/gaus-1/pandapal-bot/issues

---

## ✨ Следующие шаги после деплоя

1. ✅ Протестировать бота в Telegram
2. ✅ Проверить фронтенд на мобильных устройствах
3. 📊 Настроить аналитику (Google Analytics / Yandex Metrika)
4. 📧 Настроить уведомления об ошибках (Sentry)
5. 🔐 Настроить автоматические бэкапы БД
6. 🚀 Добавить CI/CD через GitHub Actions

---

<p align="center">
  <b>🐼 PandaPal готов к запуску! 🚀</b>
</p>

