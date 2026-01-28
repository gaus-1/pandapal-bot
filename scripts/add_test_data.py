"""
Скрипт для добавления тестовых данных в базу PostgreSQL
Запустите для быстрой проверки работы БД
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from bot.database import get_db
from bot.models import ChatHistory, User

# Устанавливаем UTF-8 для Windows консоли
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8")

# Добавляем корень проекта в PATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def add_test_data():
    """Добавить тестовые данные"""
    print("=" * 80)
    print("🎲 ДОБАВЛЕНИЕ ТЕСТОВЫХ ДАННЫХ В БАЗУ")
    print("=" * 80)
    print()

    with get_db() as db:
        # Проверяем есть ли уже данные
        existing_users = db.query(User).count()

        if existing_users > 0:
            print(f"ℹ️  В базе уже есть {existing_users} пользователей")
            response = input("Добавить еще тестовых пользователей? (y/n): ")
            if response.lower() != "y":
                print("Отменено")
                return

        print("📝 Создаём тестовых пользователей...")
        print("-" * 80)

        # Тестовый ребёнок
        child = User(
            telegram_id=100001,
            username="test_child",
            first_name="Маша",
            last_name="Тестова",
            age=10,
            grade=5,
            user_type="child",
        )
        db.add(child)
        print(f"✅ Создан ребёнок: {child.first_name} {child.last_name} (ID: {child.telegram_id})")

        # Тестовый родитель
        parent = User(
            telegram_id=100002,
            username="test_parent",
            first_name="Анна",
            last_name="Тестова",
            user_type="parent",
        )
        db.add(parent)
        print(
            f"✅ Создан родитель: {parent.first_name} {parent.last_name} (ID: {parent.telegram_id})"
        )

        # Связываем родителя и ребёнка
        child.parent_telegram_id = parent.telegram_id
        print("🔗 Связали родителя и ребёнка")

        db.commit()

        print()
        print("💬 Создаём тестовый диалог...")
        print("-" * 80)

        # Тестовые сообщения
        messages = [
            (child.telegram_id, "Привет! Помоги мне с математикой", "user"),
            (child.telegram_id, "Конечно! Чем могу помочь?", "ai"),
            (child.telegram_id, "Как решить уравнение 2x + 5 = 15?", "user"),
            (
                child.telegram_id,
                "Давай разберём пошагово:\n1. Вычтем 5 из обеих частей: 2x = 10\n2. Разделим на 2: x = 5",
                "ai",
            ),
            (child.telegram_id, "Спасибо! Теперь понятно!", "user"),
        ]

        for user_id, text, msg_type in messages:
            msg = ChatHistory(
                user_telegram_id=user_id,
                message_text=text,
                message_type=msg_type,
            )
            db.add(msg)

            icon = "👤" if msg_type == "user" else "🤖"
            preview = text[:50] + "..." if len(text) > 50 else text
            print(f"{icon} {msg_type}: {preview}")

        db.commit()

        print()
        print("=" * 80)
        print("✅ ТЕСТОВЫЕ ДАННЫЕ УСПЕШНО ДОБАВЛЕНЫ!")
        print("=" * 80)
        print()

        # Статистика
        total_users = db.query(User).count()
        total_messages = db.query(ChatHistory).count()
        children = db.query(User).filter_by(user_type="child").count()
        parents = db.query(User).filter_by(user_type="parent").count()

        print("📊 Статистика базы данных:")
        print(f"   Всего пользователей: {total_users}")
        print(f"   - Детей: {children}")
        print(f"   - Родителей: {parents}")
        print(f"   Всего сообщений: {total_messages}")
        print()

        print("🔍 Проверить данные можно в pgAdmin или командой:")
        print("   SELECT * FROM users;")
        print("   SELECT * FROM chat_history;")


if __name__ == "__main__":
    try:
        add_test_data()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
