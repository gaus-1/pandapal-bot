# Services - Бизнес-логика

Сервисный слой приложения. Вся бизнес-логика вынесена в отдельные сервисы.

## Основные сервисы

### AI сервисы
- `ai_service_solid.py` - главный сервис для работы с YandexGPT
- `yandex_cloud_service.py` - интеграция с Yandex Cloud API
- `speech_service.py` - распознавание речи (SpeechKit STT)
- `vision_service.py` - анализ изображений (Vision OCR)
- `yandex_ai_response_generator.py` - генерация ответов AI

### Модерация
- `moderation_service.py` - базовая модерация контента
- `advanced_moderation.py` - продвинутая модерация с категориями
- `ai_moderator.py` - AI-модерация через YandexGPT

### Платежи и Premium
- `payment_service.py` - интеграция с YooKassa
- `subscription_service.py` - управление Premium подписками
- `premium_features_service.py` - Premium функции

### Игры
- `games_service.py` - управление игровыми сессиями
- `game_engines.py` - игровые движки (TicTacToe, Checkers, 2048)
- `gamification_service.py` - достижения, уровни, XP

### Образование и персонализация
- `personal_tutor_service.py` - персональный репетитор, анализ слабых мест
- `bonus_lessons_service.py` - бонусные уроки для Premium
- `knowledge_service.py` - база знаний и поиск информации
- `history_service.py` - история чата и контекст

### Вспомогательные
- `translate_service.py` - перевод через Yandex Translate
- `session_service.py` - Redis сессии (Upstash)
- `user_service.py` - работа с пользователями
- `analytics_service.py` - аналитика и метрики
- `reminder_service.py` - напоминания и уведомления
- `cache_service.py` - кэширование данных
- `web_scraper.py` - парсинг веб-страниц
- `simple_engagement.py` - упрощенная система вовлечения
- `priority_support_service.py` - приоритетная поддержка для Premium

### AI инфраструктура
- `ai_context_builder.py` - построение контекста для AI
- `ai_moderator.py` - AI-модерация через YandexGPT
- `ai_request_queue.py` - очередь запросов к AI

## Паттерны

### Базовый сервис
```python
from loguru import logger

class MyService:
    def __init__(self):
        self._init_service()

    def _init_service(self):
        logger.info("Service initialized")

    async def do_something(self, param: str) -> dict:
        """Описание метода."""
        # Логика
        return {"result": "ok"}
```

### С зависимостями
```python
class ServiceA:
    def __init__(self, service_b: ServiceB):
        self.service_b = service_b
```

### Асинхронные методы
```python
async def async_method(self) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()
```

## Принципы

- Один сервис = одна ответственность
- Зависимости через конструктор (DI)
- Все публичные методы с type hints
- Документация в docstrings
- Логирование важных операций
