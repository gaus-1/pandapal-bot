# 🚀 Настройка Railway для PandaPal

## 📋 **Текущая ситуация:**

У тебя есть **ДВА компонента**:
1. **Backend (Telegram Bot)** - `web_server.py`
2. **Frontend (React сайт)** - `frontend_server.py`

## ⚠️ **Проблема:**

Сейчас на Railway один deployment, который запускает только бота. Сайт не работает.

---

## ✅ **РЕШЕНИЕ: Два отдельных сервиса на Railway**

### **Вариант 1: Два Railway сервиса (РЕКОМЕНДУЕТСЯ)**

#### **Сервис 1: Backend (Бот)**
```
Название: pandapal-bot-backend
Root Directory: /
Start Command: python web_server.py
Port: 10000
Env Variables:
  - TELEGRAM_BOT_TOKEN=<твой токен>
  - YANDEX_CLOUD_API_KEY=<ключ>
  - DATABASE_URL=<postgres url>
  - WEBHOOK_DOMAIN=pandapal-bot-backend.up.railway.app
```

#### **Сервис 2: Frontend (Сайт)**
```
Название: pandapal-frontend
Root Directory: /frontend
Build Command: npm install && npm run build
Start Command: python ../frontend_server.py
Port: 3000
```

**Railway домены:**
- Backend: `https://pandapal-bot-backend.up.railway.app`
- Frontend: `https://pandapal-frontend.up.railway.app`

**Cloudflare DNS:**
```
CNAME | pandapal.ru | pandapal-frontend.up.railway.app | Proxied ✅
CNAME | api.pandapal.ru | pandapal-bot-backend.up.railway.app | Proxied ✅
```

---

### **Вариант 2: Один сервис с двумя процессами (ПРОЩЕ)**

Можно использовать один Railway сервис, но запускать и бота, и фронтенд.

#### **Создай `start.sh`:**
```bash
#!/bin/bash

# Запускаем фронтенд на фоне
python frontend_server.py &

# Запускаем бота (основной процесс)
python web_server.py
```

#### **Обнови `Procfile`:**
```
web: bash start.sh
```

**НО:** Это не очень хорошая практика, лучше разделить.

---

## 🔧 **ЧТО НУЖНО СДЕЛАТЬ СЕЙЧАС:**

### **Шаг 1: Собери фронтенд локально**
```bash
cd frontend
npm install
npm run build
```
✅ **ГОТОВО** (уже сделано)

### **Шаг 2: Залей изменения в GitHub**
```bash
git add .
git commit -m "feat: Add frontend static server for Railway deployment"
git push origin main
```

### **Шаг 3: Зайди на Railway.app**
1. Открой проект: **pandapal-bot-production**
2. Нажми "+ New Service"
3. Выбери "GitHub Repo" → `pandapal-bot`
4. Настрой:
   - **Name:** `pandapal-frontend`
   - **Root Directory:** `/frontend`
   - **Build Command:** `npm install && npm run build`
   - **Start Command:** `python ../frontend_server.py`
5. Добавь переменную окружения:
   - `PORT=3000`

### **Шаг 4: Обнови Cloudflare DNS**
Перейди на Cloudflare → `pandapal.ru` → DNS:

**Удали старую запись:**
```
CNAME | pandapal.ru | pandapal-bot-production.up.railway.app ❌
```

**Добавь новые записи:**
```
CNAME | pandapal.ru | pandapal-frontend.up.railway.app ✅ (Proxied)
CNAME | www | pandapal.ru ✅ (Proxied)
CNAME | api | pandapal-bot-production.up.railway.app ✅ (Proxied)
```

### **Шаг 5: Обнови настройки SSL в Cloudflare**
**SSL/TLS → Overview:**
- Encryption mode: **Full (strict)**

**SSL/TLS → Edge Certificates:**
- Always Use HTTPS: **On**
- Automatic HTTPS Rewrites: **On**
- Minimum TLS Version: **1.2**

### **Шаг 6: Обнови переменные окружения бота**
Railway → `pandapal-bot-production` → Variables:
```
WEBHOOK_DOMAIN=api.pandapal.ru
FRONTEND_URL=https://pandapal.ru
```

---

## 🎯 **Результат:**

После этих шагов:

| URL | Что открывается |
|-----|-----------------|
| `https://pandapal.ru` | ✅ React сайт (фронтенд) |
| `https://api.pandapal.ru/health` | ✅ Backend health check |
| `https://api.pandapal.ru/webhook` | ✅ Telegram webhook |

---

## 📝 **Альтернатива: Vercel для фронтенда**

Если Railway ограничивает бесплатные сервисы, можно:
1. Деплоить **Frontend** на **Vercel** (бесплатно)
2. Оставить **Backend** на Railway

**Vercel:**
- Root Directory: `/frontend`
- Build Command: `npm run build`
- Output Directory: `dist`
- Framework: Vite

**Домен:**
```
CNAME | pandapal.ru | <vercel-domain>.vercel.app
```

---

## ⚙️ **Файлы готовы:**

✅ `frontend_server.py` - статический сервер для фронтенда
✅ `frontend/dist/` - собранный фронтенд
✅ `vite.config.ts` - исправлен (esbuild minify)
✅ `Procfile` - для Railway backend

---

**Выбери вариант и действуй! Нужна помощь - скажи!** 🚀
