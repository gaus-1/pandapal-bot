# 🚀 Настройка Webhook для PandaPal на Render.com

## 📋 Что нужно добавить на Render.com

### **Environment Variables (Переменные окружения)**

Зайдите на https://render.com → ваш сервис → **Environment**

Добавьте эту переменную:

```
WEBHOOK_DOMAIN=pandapal-bot.onrender.com
```

### **Готово!**

Все остальные переменные уже настроены:
- ✅ `TELEGRAM_BOT_TOKEN`
- ✅ `GEMINI_API_KEY`
- ✅ `DATABASE_URL`
- ✅ `GEMINI_MODEL`
- ✅ `PORT` (автоматически от Render)

---

## 🎯 Как это работает

### **Webhook режим:**

1. **Render запускает** `web_server.py`
2. **web_server.py импортирует** `webhook_bot.py`
3. **webhook_bot.py создает** aiohttp приложение с endpoint `/webhook`
4. **Telegram отправляет** все сообщения на `https://pandapal-bot.onrender.com/webhook`
5. **Бот обрабатывает** сообщения и отвечает

---

## ✅ Преимущества Webhook

- ✅ **Нет конфликтов** - работает с несколькими инстансами
- ✅ **Низкая нагрузка** - Telegram сам отправляет сообщения
- ✅ **Масштабируемость** - автоматически масштабируется
- ✅ **Стабильность 24/7** - профессиональный подход

---

## 🔧 Локальная разработка

Для локальной разработки используйте **Polling режим**:

```bash
python main.py
```

Polling удобнее для разработки, а Webhook - для продакшена.

---

## 🧪 Проверка работы

После деплоя проверьте:

1. **Health check:** https://pandapal-bot.onrender.com/health
2. **Webhook установлен:** В логах должно быть "Webhook URL: https://pandapal-bot.onrender.com/webhook"
3. **Бот отвечает:** Напишите боту в Telegram

---

## 🐛 Troubleshooting

### Если бот не отвечает:

1. Проверьте логи на Render: есть ли "Webhook URL"?
2. Проверьте переменную `WEBHOOK_DOMAIN` на Render
3. Убедитесь что `PORT=10000` (или Render установит автоматически)

### Если ошибка "Webhook already set":

Это нормально при первом запуске. Бот автоматически обновит webhook.

---

## 📊 Мониторинг

Endpoints для мониторинга:
- `/health` - простой health check
- `/` - то же самое

**Пример ответа:**
```json
{
  "status": "ok",
  "mode": "webhook",
  "webhook_url": "https://pandapal-bot.onrender.com/webhook"
}
```

---

## ✨ Готово!

После добавления `WEBHOOK_DOMAIN` на Render:
1. Сохраните изменения
2. Render автоматически задеплоит
3. Бот заработает через 2-3 минуты
4. Проверьте в Telegram

**Бот будет работать стабильно 24/7!** 🎉
