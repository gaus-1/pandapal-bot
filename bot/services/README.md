# Services - Бизнес-логика

Здесь вся логика приложения. Каждый сервис отвечает за свою область - AI, платежи, игры, модерация и так далее.

## Основные сервисы

### AI сервисы
- `ai_service_solid.py` - главный сервис, через него работаем с YandexGPT
- `yandex_cloud_service.py` - низкоуровневая работа с Yandex Cloud API
- `speech_service.py` - распознавание голоса (SpeechKit)
- `vision_service.py` - анализ изображений (Vision API)
- `yandex_ai_response_generator.py` - генерация ответов AI с учетом контекста

### Модерация
- `moderation_service.py` - базовая модерация, проверка на запрещенные слова
- `advanced_moderation.py` - умная модерация с категориями контента
- `ai_moderator.py` - модерация через AI, когда обычных фильтров недостаточно

### Платежи и Premium
- `payment_service.py` - работа с YooKassa (карты, СБП)
- `subscription_service.py` - управление Premium подписками
- `premium_features_service.py` - функции доступные только Premium пользователям

### Игры
- `games_service.py` - управление игровыми сессиями, сохранение прогресса
- `game_engines.py` - игровая логика (TicTacToe, Checkers, 2048)
- `gamification_service.py` - достижения, уровни, XP, мотивация

### Образование
- `personal_tutor_service.py` - персональный репетитор, анализ слабых мест ученика
- `bonus_lessons_service.py` - бонусные уроки для Premium
- `knowledge_service.py` - база знаний, поиск информации
- `history_service.py` - история чата, контекст для AI

### Вспомогательные
- `translate_service.py` - перевод через Yandex Translate
- `session_service.py` - Redis сессии для веб-сайта
- `user_service.py` - работа с пользователями
- `analytics_service.py` - аналитика, метрики, статистика
- `reminder_service.py` - напоминания пользователям
- `cache_service.py` - кэширование для ускорения
- `web_scraper.py` - парсинг веб-страниц (если нужно)
- `priority_support_service.py` - приоритетная поддержка для Premium

### AI инфраструктура
- `ai_context_builder.py` - собирает контекст для AI из истории чата
- `ai_moderator.py` - модерация через AI
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
