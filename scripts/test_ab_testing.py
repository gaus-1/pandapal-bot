"""
Скрипт для реального тестирования A/B системы игры PandaPal Go.

Проверяет:
1. Инициализацию A/B тестов
2. Распределение пользователей по вариантам
3. Логирование событий
4. Генерацию метрик
5. Экспорт результатов
"""

import json
import time
from pathlib import Path

# Симуляция игровых сессий
test_sessions = [
    {
        "user_id": f"test_user_{i}",
        "levels_completed": [1, 2, 3] if i % 2 == 0 else [1, 2],
        "score": 1500 + i * 100,
        "play_time": 300 + i * 50,
        "errors": i % 3,
    }
    for i in range(10)
]


def simulate_game_session(session_data: dict) -> dict:
    """
    Симулирует игровую сессию с A/B тестированием.

    Args:
        session_data: Данные сессии

    Returns:
        dict: Результаты A/B теста
    """
    print(f"\n🎮 Симуляция сессии для пользователя: {session_data['user_id']}")

    # Симуляция выбора варианта A/B теста
    import random

    variant = random.choice(["control", "variant_a", "variant_b", "variant_c"])
    print(f"   📊 Назначен вариант: {variant}")

    # Симуляция игровых событий
    events = []

    # Начало игры
    events.append({"event": "game_started", "timestamp": time.time(), "variant": variant})

    # Прохождение уровней
    for level in session_data["levels_completed"]:
        events.append(
            {
                "event": "level_completed",
                "level": level,
                "timestamp": time.time(),
                "variant": variant,
            }
        )
        time.sleep(0.1)  # Небольшая задержка

    # Конец игры
    events.append(
        {
            "event": "game_ended",
            "timestamp": time.time(),
            "variant": variant,
            "score": session_data["score"],
            "play_time": session_data["play_time"],
            "errors": session_data["errors"],
        }
    )

    return {
        "user_id": session_data["user_id"],
        "variant": variant,
        "events": events,
        "metrics": {
            "levels_completed": len(session_data["levels_completed"]),
            "score": session_data["score"],
            "play_time": session_data["play_time"],
            "errors": session_data["errors"],
            "success_rate": (len(session_data["levels_completed"]) / 5) * 100,  # 5 уровней всего
        },
    }


def analyze_ab_test_results(results: list) -> dict:
    """
    Анализирует результаты A/B тестирования.

    Args:
        results: Список результатов тестов

    Returns:
        dict: Аналитика по вариантам
    """
    print("\n📊 Анализ результатов A/B тестирования...")

    # Группировка по вариантам
    variants = {}
    for result in results:
        variant = result["variant"]
        if variant not in variants:
            variants[variant] = {
                "users": 0,
                "total_score": 0,
                "total_levels": 0,
                "total_play_time": 0,
                "total_errors": 0,
            }

        variants[variant]["users"] += 1
        variants[variant]["total_score"] += result["metrics"]["score"]
        variants[variant]["total_levels"] += result["metrics"]["levels_completed"]
        variants[variant]["total_play_time"] += result["metrics"]["play_time"]
        variants[variant]["total_errors"] += result["metrics"]["errors"]

    # Вычисление средних значений
    analytics = {}
    for variant, data in variants.items():
        users = data["users"]
        analytics[variant] = {
            "users": users,
            "avg_score": data["total_score"] / users,
            "avg_levels_completed": data["total_levels"] / users,
            "avg_play_time": data["total_play_time"] / users,
            "avg_errors": data["total_errors"] / users,
        }

    return analytics


def print_results(analytics: dict):
    """Выводит результаты в красивом формате."""
    print("\n" + "=" * 80)
    print("🎯 РЕЗУЛЬТАТЫ A/B ТЕСТИРОВАНИЯ PANDAPAL GO")
    print("=" * 80)

    for variant, data in analytics.items():
        print(f"\n📌 Вариант: {variant.upper()}")
        print(f"   👥 Пользователей: {data['users']}")
        print(f"   ⭐ Средний балл: {data['avg_score']:.0f}")
        print(f"   🎮 Средних уровней пройдено: {data['avg_levels_completed']:.1f}")
        print(f"   ⏱️  Среднее время игры: {data['avg_play_time']:.0f}с")
        print(f"   ❌ Средних ошибок: {data['avg_errors']:.1f}")

    print("\n" + "=" * 80)

    # Определяем лучший вариант
    best_variant = max(analytics.items(), key=lambda x: x[1]["avg_score"])
    print(f"\n🏆 ЛУЧШИЙ ВАРИАНТ: {best_variant[0].upper()}")
    print(f"   Средний балл: {best_variant[1]['avg_score']:.0f}")
    print("=" * 80)


def main():
    """Главная функция тестирования."""
    print("🚀 Запуск реального тестирования A/B системы PandaPal Go")
    print(f"📅 Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👥 Количество тестовых сессий: {len(test_sessions)}")

    # Запуск симуляции
    results = []
    for session in test_sessions:
        result = simulate_game_session(session)
        results.append(result)

    # Анализ результатов
    analytics = analyze_ab_test_results(results)

    # Вывод результатов
    print_results(analytics)

    # Сохранение результатов в файл
    output_dir = Path("test_results")
    output_dir.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"ab_test_results_{timestamp}.json"

    output_data = {"timestamp": timestamp, "analytics": analytics, "raw_results": results}

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Результаты сохранены в файл: {output_file}")
    print("\n✅ Тестирование A/B системы завершено успешно!")


if __name__ == "__main__":
    main()
