# SQL Scripts (legacy / backup)

**Схема БД управляется только через Alembic.** Эти скрипты приложением не используются.

- Единый источник правды: `alembic/versions/`
- Для применения схемы: `alembic upgrade head`
- Папка `sql/` — архив/бэкап для ручного восстановления или справки

## Файлы (только справка)

- `01_drop_all_tables.sql`, `02_create_tables.sql` — создание таблиц (устарело)
- `03_*` … `06_*`, `05a_*` — миграции по фичам (дублируют Alembic)
- `07_add_pgvector_tables.sql` — pgvector (embedding_cache, knowledge_embeddings). Требует PostgreSQL с pgvector. Запуск: `python scripts/run_pgvector_sql.py` или `alembic upgrade head`
- `subscriptions.csv` — данные планов подписок

## Важно

- Для любых изменений схемы используйте Alembic: новая миграция и `alembic upgrade head`
- Перед ручным применением скриптов — бэкап и проверка на staging
