#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Простая инициализация базы данных."""

import os
import sys

# Добавляем текущую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем переменную окружения для SQLite
os.environ.setdefault("DATABASE_URL", "sqlite:///./pandapal_dev.db")

try:
    from sqlalchemy import create_engine

    from bot.models import Base

    # Создаём engine для SQLite
    engine = create_engine("sqlite:///./pandapal_dev.db", echo=True)

    # Создаём все таблицы
    print("Создание таблиц...")
    Base.metadata.create_all(bind=engine)

    print("\nБаза данных успешно инициализирована!")
    print(f"Создано таблиц: {len(Base.metadata.tables)}")
    print("\nСписок таблиц:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")

except Exception as e:
    print(f"Ошибка: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
