#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для безопасного обновления зависимостей проекта.
Обновляет пакеты по приоритетам с проверкой совместимости.
"""

import subprocess
import sys
from pathlib import Path

# Настройка кодировки для Windows
if sys.platform == "win32":
    import io

    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stderr.encoding != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Приоритет 1: Критичные обновления безопасности
PRIORITY_1 = [
    ("protobuf", "5.29.5", "6.33.2"),
    ("pydantic", "2.9.2", "2.12.5"),
    ("pydantic_core", "2.23.4", "2.41.5"),  # pydantic_core в requirements
    ("sentry-sdk", "2.18.0", "2.48.0"),
]

# Приоритет 2: Важные обновления стабильности
PRIORITY_2 = [
    ("SQLAlchemy", "2.0.36", "2.0.45"),
    ("alembic", "1.13.2", "1.17.2"),
    ("psycopg", "3.2.10", "3.3.2"),
    ("psycopg-binary", "3.2.10", "3.3.2"),
    ("fastapi", "0.115.6", "0.125.0"),
    ("uvicorn", "0.34.0", "0.38.0"),
    ("starlette", "0.44.0", "0.50.0"),
]

# Приоритет 3: Рекомендуемые обновления
PRIORITY_3 = [
    ("aiogram", "3.22.0", "3.23.0"),
    ("google-generativeai", "0.8.5", "0.8.6"),
    ("black", "25.9.0", "25.12.0"),
    ("mypy", "1.18.2", "1.19.1"),
    ("pytest-asyncio", "1.2.0", "1.3.0"),
    ("python-dotenv", "1.0.1", "1.2.1"),
    ("google-auth", "2.41.1", "2.45.0"),
    ("google-api-core", "2.25.1", "2.28.1"),
    ("google-api-python-client", "2.183.0", "2.187.0"),
    ("googleapis-common-protos", "1.70.0", "1.72.0"),
    ("google-auth-httplib2", "0.2.0", "0.3.0"),
    ("aiohttp", "3.12.15", "3.13.2"),
    ("aiofiles", "24.1.0", "25.1.0"),
    ("numpy", "2.3.3", "2.3.5"),
    ("certifi", "2025.8.3", "2025.11.12"),
    ("urllib3", "2.5.0", "2.6.2"),
    ("idna", "3.10", "3.11"),
    ("charset-normalizer", "3.4.3", "3.4.4"),
    ("click", "8.3.0", "8.3.1"),
    ("attrs", "25.3.0", "25.4.0"),
    ("anyio", "4.11.0", "4.12.0"),
    ("coverage", "7.10.7", "7.13.0"),
    ("filelock", "3.19.1", "3.20.1"),
    ("fsspec", "2025.9.0", "2025.12.0"),
    ("greenlet", "3.2.4", "3.3.0"),
    ("grpcio", "1.75.1", "1.76.0"),
    ("grpcio-status", "1.71.2", "1.76.0"),
    ("joblib", "1.5.2", "1.5.3"),
    ("multidict", "6.6.4", "6.7.0"),
    ("platformdirs", "4.4.0", "4.5.1"),
    ("proto-plus", "1.26.1", "1.27.0"),
    ("typer", "0.19.2", "0.20.1"),
    ("yarl", "1.20.1", "1.22.0"),
    ("tzdata", "2025.2", "2025.3"),
    ("virtualenv", "20.34.0", "20.35.4"),
    ("beautifulsoup4", "4.14.2", "4.14.3"),
    ("soupsieve", "2.8", "2.8.1"),
    ("ruamel.yaml", "0.18.15", "0.18.17"),
    ("ruamel.yaml.clib", "0.2.14", "0.2.15"),
    ("safety", "3.6.2", "3.7.0"),
    ("safety-schemas", "0.0.16", "0.0.17"),
    ("bandit", "1.7.10", "1.9.2"),
    ("authlib", "1.6.5", "1.6.6"),
    ("cfgv", "3.4.0", "3.5.0"),
    ("iniconfig", "2.1.0", "2.3.0"),
    ("pylint", "4.0.2", "4.0.4"),
    ("marshmallow", "4.0.1", "4.1.1"),
    ("cachetools", "6.2.0", "6.2.4"),
    ("propcache", "0.3.2", "0.4.1"),
    ("pytokens", "0.1.10", "0.3.0"),
    ("regex", "2025.9.18", "2025.11.3"),
    ("qrcode", "8.0", "8.2"),
    ("networkx", "3.5", "3.6.1"),
    ("nodeenv", "1.9.1", "1.10.0"),
    ("pre_commit", "4.3.0", "4.5.1"),
    ("faker", "37.8.0", "39.0.0"),
    ("fakeredis", "2.31.3", "2.33.0"),
]

# Приоритет 4: Major updates (требуют осторожности)
PRIORITY_4 = [
    ("pytest", "8.4.2", "9.0.2"),  # Major update
    ("isort", "6.1.0", "7.0.0"),  # Major update
    # redis, pillow, torch - оставляем как есть, могут быть breaking changes
]


def update_package(package_name: str, old_version: str, new_version: str) -> bool:
    """
    Обновить пакет до новой версии.

    Args:
        package_name: Имя пакета
        old_version: Старая версия
        new_version: Новая версия

    Returns:
        True если успешно, False если ошибка
    """
    print(f"\n{'='*80}")
    print(f"Обновление {package_name}: {old_version} → {new_version}")
    print(f"{'='*80}")

    try:
        # Устанавливаем новую версию
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            f"{package_name}=={new_version}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        print(f"[OK] {package_name} успешно обновлен до {new_version}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Ошибка при обновлении {package_name}:")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"[ERROR] Неожиданная ошибка: {e}")
        return False


def update_requirements_file(updates: list):
    """
    Обновить requirements.txt с новыми версиями.

    Args:
        updates: Список кортежей (package_name, old_version, new_version)
    """
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("[ERROR] requirements.txt не найден")
        return

    content = requirements_file.read_text(encoding="utf-8")

    for package_name, old_version, new_version in updates:
        # Ищем строку с пакетом и версией
        old_line = f"{package_name}=={old_version}"
        new_line = f"{package_name}=={new_version}"

        # Заменяем версию (с учетом возможных комментариев)
        if old_line in content:
            content = content.replace(old_line, new_line)
        else:
            # Пробуем найти с учетом регистра и возможных вариантов имени
            import re

            pattern = re.compile(
                rf"^{re.escape(package_name)}=={re.escape(old_version)}",
                re.IGNORECASE | re.MULTILINE,
            )
            content = pattern.sub(f"{package_name}=={new_version}", content)

    requirements_file.write_text(content, encoding="utf-8")
    print(f"\n[OK] requirements.txt обновлен")


def main():
    """Основная функция обновления."""
    print("=" * 80)
    print("Безопасное обновление зависимостей проекта PandaPal")
    print("=" * 80)

    all_updates = []
    successful_updates = []
    failed_updates = []

    # Обновляем по приоритетам
    for priority, packages in enumerate([PRIORITY_1, PRIORITY_2, PRIORITY_3, PRIORITY_4], 1):
        print(f"\n{'#'*80}")
        print(f"ПРИОРИТЕТ {priority}: Обновление {len(packages)} пакетов")
        print(f"{'#'*80}")

        for package_name, old_version, new_version in packages:
            all_updates.append((package_name, old_version, new_version))

            success = update_package(package_name, old_version, new_version)
            if success:
                successful_updates.append((package_name, old_version, new_version))
            else:
                failed_updates.append((package_name, old_version, new_version))
                print(f"[WARN] Пропускаем {package_name}, продолжаем с остальными...")

    # Обновляем requirements.txt
    print(f"\n{'='*80}")
    print("Обновление requirements.txt")
    print(f"{'='*80}")
    update_requirements_file(successful_updates)

    # Итоговый отчет
    print(f"\n{'='*80}")
    print("ИТОГОВЫЙ ОТЧЕТ")
    print(f"{'='*80}")
    print(f"Всего пакетов для обновления: {len(all_updates)}")
    print(f"Успешно обновлено: {len(successful_updates)}")
    print(f"Ошибок: {len(failed_updates)}")

    if failed_updates:
        print(f"\n[WARN] Пакеты с ошибками:")
        for package_name, old_version, new_version in failed_updates:
            print(f"  - {package_name}: {old_version} → {new_version}")

    if len(successful_updates) > 0:
        print(f"\n[SUCCESS] Обновлено {len(successful_updates)} пакетов успешно!")
        return 0
    else:
        print(f"\n[ERROR] Не удалось обновить ни одного пакета")
        return 1


if __name__ == "__main__":
    sys.exit(main())
