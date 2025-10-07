# 🚀 Исправленный деплой на Render

## Проблема
Render не мог найти открытый порт для бота, что приводило к ошибке "Port scan timeout reached, no open ports detected".

## Решение

### 1. Создан `web_server.py`
Простой веб-сервер на `aiohttp`, который:
- Открывает порт для Render
- Запускает бота в фоновом режиме
- Предоставляет health check endpoint

### 2. Обновлен `render.yaml`
```yaml
services:
  - type: web
    name: pandapal-bot
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python web_server.py
    healthCheckPath: /health
    autoDeploy: true
```

### 3. Health Check Endpoints
- `GET /health` - проверка состояния сервера
- `GET /` - главная страница (тот же health check)

## Как это работает

1. **Render запускает** `python web_server.py`
2. **Веб-сервер** открывает порт (из переменной `PORT`)
3. **Бот запускается** в фоновом режиме через `asyncio.create_task()`
4. **Render видит** открытый порт и считает деплой успешным
5. **Бот работает** параллельно с веб-сервером

## Переменные окружения на Render

Убедитесь, что настроены:
- `DATABASE_URL` - URL базы данных PostgreSQL
- `TELEGRAM_BOT_TOKEN` - токен бота
- `GEMINI_API_KEY` - API ключ Google Gemini
- `SECRET_KEY` - секретный ключ приложения

## Мониторинг

После деплоя проверьте:
- https://pandapal-bot.onrender.com/health
- Логи в Render Dashboard
- Работу бота в Telegram

## Тестирование локально

```bash
# Активируйте виртуальное окружение
.\venv\Scripts\Activate.ps1

# Запустите тестовый сервер
python test_server.py

# Проверьте health check
Invoke-WebRequest -Uri "http://localhost:8000/health"
```

## Если что-то не работает

1. Проверьте логи в Render Dashboard
2. Убедитесь, что все переменные окружения настроены
3. Проверьте, что `requirements.txt` содержит все зависимости
4. Убедитесь, что `main.py` работает локально

---

✅ **Статус**: Исправлено и готово к деплою!
