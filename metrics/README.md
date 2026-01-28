# Metrics - Метрики

Папка для работы с бизнес-метриками проекта.

## Структура

```
metrics/
├── exports/      # Экспортированные метрики (CSV, JSON)
├── reports/      # Отчеты по метрикам
└── dashboards/   # Дашборды
```

## Использование

### Просмотр метрик

```bash
# Все метрики за 7 дней
python scripts/view_analytics_metrics.py

# Только безопасность
python scripts/view_analytics_metrics.py --type safety

# За 30 дней
python scripts/view_analytics_metrics.py --days 30
```

### Экспорт метрик

```bash
python scripts/export_metrics.py
```

## Типы метрик

- Безопасность (safety) - заблокированные сообщения
- Образование (education) - AI взаимодействия
- Родители (parent) - просмотры дашборда
- Технические (technical) - системные метрики

## Важно

- Метрики записываются автоматически 24/7
- Данные хранятся в таблице `analytics_metrics` в PostgreSQL
- Ошибки записи не ломают основной функционал
