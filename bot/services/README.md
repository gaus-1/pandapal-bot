# Services - Бизнес-логика

Вся логика приложения. Каждый сервис отвечает за свою область - AI, платежи, игры, модерация и так далее.

## Основные сервисы

### AI сервисы
- `ai_service_solid.py` - главный сервис, через него работаем с YandexGPT (Facade паттерн)
- `yandex_cloud_service.py` - низкоуровневая работа с Yandex Cloud API (streaming/non-streaming, Vision, SpeechKit)
- `yandex_ai_response_generator.py` - генерация ответов AI с учетом контекста, истории чата, возраста, очистка от повторов
- `speech_service.py` - распознавание голоса через Yandex SpeechKit STT (WebM → OGG конвертация)
- `vision_service.py` - анализ изображений через Yandex Vision API (OCR + GPT анализ)
- `ai_context_builder.py` - сбор контекста для AI из истории чата
- `ai_request_queue.py` - очередь запросов для предотвращения перегрузки API

### Модерация
- `moderation_service.py` - базовая модерация, проверка на запрещенные слова
- `advanced_moderation.py` - умная модерация с категориями контента
- `ai_moderator.py` - модерация через AI, когда обычных фильтров недостаточно

### Платежи и Premium
- `payment_service.py` - работа с YooKassa (продакшн режим, карты, СБП, сохранение карт, webhooks)
- `subscription_service.py` - управление Premium подписками (активация, деактивация, проверка статуса)
- `premium_features_service.py` - проверка Premium статуса и лимитов (50/500/unlimited запросов в день)

### Игры
- `games_service.py` - управление игровыми сессиями, сохранение прогресса, проверка игровых достижений
- `game_engines.py` - игровая логика (TicTacToe, Checkers, 2048) с AI противниками
- `gamification_service.py` - достижения, уровни, XP, мотивация (исправлена логика: игровые достижения не проверяются при AI ответах)

### Образование
- `personal_tutor_service.py` - персональный репетитор, анализ слабых мест ученика
- `bonus_lessons_service.py` - бонусные уроки для Premium
- `knowledge_service.py` - база знаний, поиск информации из веб-источников
- `history_service.py` - история чата, контекст для AI

### Вспомогательные
- `translate_service.py` - перевод через Yandex Translate с автоопределением языка
- `session_service.py` - Redis сессии для веб-сайта
- `user_service.py` - работа с пользователями
- `analytics_service.py` - аналитика, метрики, статистика
- `reminder_service.py` - напоминания пользователям
- `cache_service.py` - кэширование для ускорения
- `web_scraper.py` - парсинг веб-страниц для knowledge service
- `priority_support_service.py` - приоритетная поддержка для Premium

### AI инфраструктура
- `ai_context_builder.py` - собирает контекст для AI из истории чата
- `ai_request_queue.py` - очередь запросов, чтобы не перегружать API

## Как писать сервисы

### Простой сервис

```python
from loguru import logger

class MyService:
    def __init__(self):
        logger.info("Инициализация сервиса")

    async def do_something(self, param: str) -> dict:
        """Что делает метод."""
        # Твоя логика здесь
        return {"result": "ok"}
```

### С зависимостями

Если сервису нужен другой сервис, передавай через конструктор:

```python
class ServiceA:
    def __init__(self, service_b: ServiceB):
        self.service_b = service_b
```

### Асинхронные методы

Для работы с внешними API используй async:

```python
async def fetch_data(self) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()
```

## Важно помнить

- Один сервис = одна задача. Не смешивай логику платежей и игр.
- Всегда используй type hints - так проще понять что ожидает функция.
- Логируй важные операции - это поможет отладить проблемы.
- Обрабатывай ошибки - не падай молча, логируй и возвращай понятные сообщения.
