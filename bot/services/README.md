# Services - Бизнес-логика

Вся логика приложения. Каждый сервис отвечает за свою область - AI, платежи, игры, модерация и так далее.

## Основные сервисы

### Генерация ответов и контекст
- `ai_service_solid.py` — фасад над Yandex Cloud (YandexGPT, Vision, SpeechKit)
- `yandex_cloud_service.py` — низкоуровневая работа с Yandex Cloud API (streaming/non-streaming, Vision, SpeechKit)
- `yandex_ai_response_generator.py` — генерация ответов с учётом контекста, истории, возраста, дедупликация
- `speech_service.py` — распознавание голоса через Yandex SpeechKit STT (WebM → OGG)
- `vision_service.py` — анализ изображений через Yandex Vision API (OCR + анализ)
- `ai_context_builder.py` — сбор контекста из истории чата
- `ai_request_queue.py` — очередь запросов для предотвращения перегрузки API

### Модерация
- `moderation_service.py` — базовая модерация, проверка на запрещённые слова
- `advanced_moderation.py` — модерация с категориями контента
- `ai_moderator.py` — модерация через модель, когда фильтров недостаточно

### Платежи и Premium
- `payment_service.py` - работа с YooKassa (продакшн режим, карты, СБП, сохранение карт, webhooks)
- `subscription_service.py` - управление Premium подписками (активация, деактивация, проверка статуса)
- `premium_features_service.py` — проверка Premium статуса и лимитов (30 запросов/месяц free, 500/день Premium 299 ₽/мес)

### Игры
- `games_service.py` — управление игровыми сессиями, сохранение прогресса, проверка игровых достижений
- `game_engines/` — игровая логика (TicTacToe, Checkers, 2048, Erudite) с умным противником
- `gamification_service.py` — достижения, уровни, XP, мотивация

### Образование
- `personal_tutor_service.py` — персональный репетитор, анализ слабых мест ученика
- `bonus_lessons_service.py` — бонусные уроки для Premium
- `knowledge_service.py` — база знаний, поиск из веб-источников, Wikipedia, enhanced RAG
- `history_service.py` — история чата, контекст для генерации ответов
- `homework_service.py` — проверка домашних заданий по фото
- `adaptive_learning_service.py` — отслеживание проблемных тем, адаптация сложности
- `adult_topics_service.py` — объяснение взрослых тем (деньги, ЖКУ, документы) простыми словами
- `visualization/` — генерация графиков, таблиц, карт, диаграмм по предметам
- `rag/` — enhanced RAG (query_expander, reranker, semantic_cache, compressor)
- `prompt_builder.py` — сборка системного промпта под контекст
- `yandex_art_service.py` — генерация изображений по описанию (YandexART)

### Вспомогательные
- `translate_service.py` - перевод через Yandex Translate с автоопределением языка
- `session_service.py` - Redis сессии для веб-сайта
- `user_service.py` - работа с пользователями
- `analytics_service.py` - аналитика, метрики, статистика
- `reminder_service.py` - напоминания пользователям
- `cache_service.py` - кэширование для ускорения
- `web_scraper.py` - парсинг веб-страниц для knowledge service
- `priority_support_service.py` - приоритетная поддержка для Premium

### Mini App сервисы
- `miniapp/` — intent_service, photo_service, chat_context_service, audio_service, visualization_service

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
