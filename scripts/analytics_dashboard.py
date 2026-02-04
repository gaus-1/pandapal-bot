"""
Простой дашборд для просмотра статистики PandaPal
Использование: python scripts/analytics_dashboard.py
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


def get_stats():
    """Получение и отображение основной статистики"""

    # Подключение к БД
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL не найден в .env")
        return

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            print("\n" + "=" * 70)
            print("📊 СТАТИСТИКА PANDAPAL".center(70))
            print("=" * 70)
            print(f"🕐 Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
            print("=" * 70)

            # ПОЛЬЗОВАТЕЛИ
            total_users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
            active_users = (
                conn.execute(text("SELECT COUNT(*) FROM users WHERE is_active = true")).scalar()
                or 0
            )

            # По типам
            children = (
                conn.execute(text("SELECT COUNT(*) FROM users WHERE user_type = 'child'")).scalar()
                or 0
            )
            parents = (
                conn.execute(text("SELECT COUNT(*) FROM users WHERE user_type = 'parent'")).scalar()
                or 0
            )
            teachers = (
                conn.execute(
                    text("SELECT COUNT(*) FROM users WHERE user_type = 'teacher'")
                ).scalar()
                or 0
            )

            # Новые за период
            week_ago = datetime.now() - timedelta(days=7)
            new_users_week = (
                conn.execute(
                    text("SELECT COUNT(*) FROM users WHERE created_at >= :week_ago"),
                    {"week_ago": week_ago},
                ).scalar()
                or 0
            )

            print(f"\n👥 ПОЛЬЗОВАТЕЛИ:")
            print(f"   Всего:              {total_users:>6}")
            print(f"   Активных:           {active_users:>6}")
            print(f"   Новых за неделю:    {new_users_week:>6}")
            print(f"\n   По типам:")
            print(f"   • Дети:             {children:>6}")
            print(f"   • Родители:         {parents:>6}")
            print(f"   • Учителя:          {teachers:>6}")

            # Сообщения
            total_messages = conn.execute(text("SELECT COUNT(*) FROM chat_history")).scalar() or 0

            today = datetime.now().date()
            messages_today = (
                conn.execute(
                    text("SELECT COUNT(*) FROM chat_history WHERE DATE(timestamp) = :today"),
                    {"today": today},
                ).scalar()
                or 0
            )

            messages_week = (
                conn.execute(
                    text("SELECT COUNT(*) FROM chat_history WHERE timestamp >= :week_ago"),
                    {"week_ago": week_ago},
                ).scalar()
                or 0
            )

            user_msgs = (
                conn.execute(
                    text("SELECT COUNT(*) FROM chat_history WHERE message_type = 'user'")
                ).scalar()
                or 0
            )

            ai_msgs = (
                conn.execute(
                    text("SELECT COUNT(*) FROM chat_history WHERE message_type = 'ai'")
                ).scalar()
                or 0
            )

            print(f"\n💬 СООБЩЕНИЯ:")
            print(f"   Всего:              {total_messages:>6}")
            print(f"   Сегодня:            {messages_today:>6}")
            print(f"   За неделю:          {messages_week:>6}")
            print(f"\n   По типам:")
            print(f"   • От пользователей: {user_msgs:>6}")
            print(f"   • От AI:            {ai_msgs:>6}")

            # СРЕДНИЕ ПОКАЗАТЕЛИ
            if total_users > 0:
                avg_messages_per_user = total_messages / total_users
                print(f"\n📊 СРЕДНИЕ ПОКАЗАТЕЛИ:")
                print(f"   Сообщений на пользователя: {avg_messages_per_user:.1f}")

            # ТОП АКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ
            result = conn.execute(
                text(
                    """
                SELECT
                    u.first_name,
                    u.telegram_id,
                    u.user_type,
                    COUNT(ch.id) as msg_count,
                    MAX(ch.timestamp) as last_message
                FROM users u
                LEFT JOIN chat_history ch ON u.telegram_id = ch.user_telegram_id
                GROUP BY u.telegram_id, u.first_name, u.user_type
                ORDER BY msg_count DESC
                LIMIT 15
            """
                )
            )

            print(f"\n🏆 ТОП-15 АКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ:")
            print(f"{'№':<4} {'Имя':<20} {'Тип':<10} {'Сообщений':<12} {'Последнее сообщение'}")
            print("-" * 70)

            for i, row in enumerate(result, 1):
                name = row[0] or "Неизвестно"
                user_type = row[2] or "child"
                msg_count = row[3] or 0
                last_msg = row[4].strftime("%d.%m %H:%M") if row[4] else "Нет"

                print(f"{i:<4} {name:<20} {user_type:<10} {msg_count:<12} {last_msg}")

            # АКТИВНОСТЬ ПО ДНЯМ
            result = conn.execute(
                text(
                    """
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as messages
                FROM chat_history
                WHERE timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """
                )
            )

            print(f"\n📅 АКТИВНОСТЬ ПО ДНЯМ (последние 7 дней):")
            print(f"{'Дата':<15} {'Сообщений':<12} {'График'}")
            print("-" * 70)

            max_messages = 1
            days_data = list(result)
            if days_data:
                max_messages = max(row[1] for row in days_data)

            for row in days_data:
                date = row[0].strftime("%d.%m.%Y")
                messages = row[1]
                bar_length = int((messages / max_messages) * 40) if max_messages > 0 else 0
                bar = "█" * bar_length

                print(f"{date:<15} {messages:<12} {bar}")

            # АКТИВНОСТЬ ПО ЧАСАМ (сегодня)
            result = conn.execute(
                text(
                    """
                SELECT
                    EXTRACT(HOUR FROM timestamp) as hour,
                    COUNT(*) as messages
                FROM chat_history
                WHERE DATE(timestamp) = :today
                GROUP BY EXTRACT(HOUR FROM timestamp)
                ORDER BY hour
            """
                ),
                {"today": today},
            )

            hours_data = {int(row[0]): row[1] for row in result}

            if hours_data:
                print(f"\n🕐 АКТИВНОСТЬ ПО ЧАСАМ (сегодня):")
                print(f"{'Час':<8} {'Сообщений':<12} {'График'}")
                print("-" * 70)

                max_hour_messages = max(hours_data.values()) if hours_data else 1

                for hour in range(24):
                    messages = hours_data.get(hour, 0)
                    bar_length = (
                        int((messages / max_hour_messages) * 30) if max_hour_messages > 0 else 0
                    )
                    bar = "▓" * bar_length

                    print(f"{hour:02d}:00   {messages:<12} {bar}")

            print("\n" + "=" * 70)
            print("✅ Статистика обновлена".center(70))
            print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Ошибка получения статистики: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Загрузка статистики PandaPal...\n")
    get_stats()
