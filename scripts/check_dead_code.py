"""
Скрипт для поиска и отчета мертвого кода в проекте.

Использует vulture для обнаружения неиспользуемых функций, классов,
переменных и импортов в Python коде.
"""

import subprocess
import sys


def find_dead_code():
    """Найти мертвый код в проекте."""
    print("=" * 60)
    print("POISK MERTVOGO KODA (Dead Code Detection)")
    print("=" * 60)

    cmd = [
        "vulture",
        "bot",
        ".vulture_whitelist.py",
        "--min-confidence",
        "80",
        "--exclude",
        "*_OLD.py,*/alembic/*,*/tests/*",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

        if result.returncode == 0:
            print("OK: MERTVYY KOD NE NAYDEN!")
            print("   Proekt chistyy i optimalnyy!")
            return 0
        else:
            print("WARNING: NAYDEN MERTVYY KOD:")
            print("-" * 60)
            print(result.stdout)
            print("-" * 60)
            count = result.stdout.count("unused")
            print(f"   Naydeno problem: {count}")
            print("   Rekomendatsiya: Udali neispolzuemyy kod ili dobav v .vulture_whitelist.py")
            return 1

    except FileNotFoundError:
        print("ERROR: vulture ne ustanovlen!")
        print("   Ustanovi: pip install vulture")
        return 2
    except Exception as e:
        print(f"ERROR: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(find_dead_code())
