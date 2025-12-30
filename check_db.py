#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт для проверки структуры базы данных PandaPal."""

import sqlite3
import sys
from pathlib import Path

# Настройка кодировки для Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def check_sqlite_db(db_path: str):
    """Проверка SQLite базы данных."""
    print(f"Проверка SQLite базы: {db_path}\n")

    if not Path(db_path).exists():
        print(f"❌ База данных не найдена: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        print(f"Найдено таблиц: {len(tables)}\n")

        for table in tables:
            table_name = table[0]
            print(f"Таблица: {table_name}")

            # Получаем структуру таблицы
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            print(f"   Колонок: {len(columns)}")
            for col in columns:
                col_id, col_name, col_type, not_null, default, pk = col
                print(f"   - {col_name}: {col_type}" + (" [PK]" if pk else ""))

            # Считаем записи
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   Записей: {count}\n")

        conn.close()
        print("Проверка завершена успешно!")

    except Exception as e:
        print(f"❌ Ошибка при проверке базы: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Проверяем SQLite базу
    check_sqlite_db("pandapal_dev.db")
