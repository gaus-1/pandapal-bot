#!/usr/bin/env python3
"""
Диагностика основной БД (PostgreSQL). Проверяет подключение и сохранение сообщений.
Для SQLite/локальной БД см. check_db.py.
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import func

from bot.database import get_db
from bot.models import ChatHistory

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="INFO",
)


def check_database():
    """Проверка состояния базы данных."""
    print("\n" + "=" * 60)
    print("🔍 ДИАГНОСТИКА БАЗЫ ДАННЫХ")
    print("=" * 60 + "\n")

    try:
        with get_db() as db:
            # 1. Проверка текущей БД
            result = db.execute(func.current_database())
            db_name = result.scalar()
            print(f"📊 Текущая база данных: {db_name}")

            # 2. Проверка максимального ID
            max_id_result = db.query(func.max(ChatHistory.id)).scalar()
            total_count = db.query(func.count(ChatHistory.id)).scalar()
            print(f"📊 Максимальный ID в chat_history: {max_id_result}")
            print(f"📊 Всего сообщений: {total_count}")

            # 3. Последние 10 записей по ID
            print("\n📝 Последние 10 записей (по ID):")
            print("-" * 60)
            recent = db.query(ChatHistory).order_by(ChatHistory.id.desc()).limit(10).all()
            if recent:
                for msg in recent:
                    preview = (
                        msg.message_text[:50] + "..."
                        if len(msg.message_text) > 50
                        else msg.message_text
                    )
                    print(
                        f"ID: {msg.id:4d} | User: {msg.user_telegram_id} | Type: {msg.message_type:4s} | {preview}"
                    )
            else:
                print("❌ Записей не найдено!")

            # 4. Проверка для конкретного пользователя
            telegram_id = 963126718
            print(f"\n👤 Последние 10 сообщений для пользователя {telegram_id}:")
            print("-" * 60)
            user_messages = (
                db.query(ChatHistory)
                .filter(ChatHistory.user_telegram_id == telegram_id)
                .order_by(ChatHistory.timestamp.desc())
                .limit(10)
                .all()
            )
            if user_messages:
                for msg in user_messages:
                    preview = (
                        msg.message_text[:50] + "..."
                        if len(msg.message_text) > 50
                        else msg.message_text
                    )
                    print(
                        f"ID: {msg.id:4d} | Type: {msg.message_type:4s} | Time: {msg.timestamp} | {preview}"
                    )
            else:
                print(f"❌ Сообщений для пользователя {telegram_id} не найдено!")

            # 5. Проверка записей с ID >= 299 (из логов)
            print(f"\n🔍 Проверка записей с ID >= 299 (из логов):")
            print("-" * 60)
            log_messages = (
                db.query(ChatHistory)
                .filter(ChatHistory.id >= 299)
                .order_by(ChatHistory.id.asc())
                .all()
            )
            if log_messages:
                print(f"✅ Найдено {len(log_messages)} записей:")
                for msg in log_messages:
                    preview = (
                        msg.message_text[:30] + "..."
                        if len(msg.message_text) > 30
                        else msg.message_text
                    )
                    print(
                        f"  ID: {msg.id:4d} | User: {msg.user_telegram_id} | Type: {msg.message_type:4s} | {preview}"
                    )
            else:
                print("❌ Записи с ID >= 299 не найдены!")

            # 6. Статистика по типам сообщений
            print(f"\n📊 Статистика по типам сообщений:")
            print("-" * 60)
            stats = (
                db.query(ChatHistory.message_type, func.count(ChatHistory.id).label("count"))
                .group_by(ChatHistory.message_type)
                .all()
            )
            for msg_type, count in stats:
                print(f"  {msg_type:4s}: {count:5d} сообщений")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("✅ Диагностика завершена")
    print("=" * 60 + "\n")
    return True


if __name__ == "__main__":
    check_database()
