"""Скрипт для сброса истории Alembic миграций"""
from sqlalchemy import create_engine, text
from bot.config import settings

engine = create_engine(settings.database_url)

with engine.connect() as conn:
    # Удаляем таблицу версий Alembic
    conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    conn.commit()
    print("✅ История миграций Alembic очищена")

