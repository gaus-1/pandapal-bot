#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки актуальности версий пакетов в requirements.txt.
Сравнивает текущие версии с последними доступными на PyPI.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from packaging import version

# Настройка кодировки для Windows
if sys.platform == "win32":
    import io

    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stderr.encoding != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Добавляем корневую папку в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def get_latest_version(package_name: str) -> Tuple[str, bool]:
    """
    Получить последнюю версию пакета с PyPI.

    Args:
        package_name: Имя пакета

    Returns:
        Tuple[latest_version, success]: Последняя версия и флаг успеха
    """
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        latest_version = data["info"]["version"]
        return latest_version, True
    except Exception as e:
        return f"ERROR: {e}", False


def parse_requirements(requirements_file: Path) -> Dict[str, str]:
    """
    Парсит requirements.txt и извлекает пакеты с версиями.

    Args:
        requirements_file: Путь к requirements.txt

    Returns:
        Dict[package_name, version]: Словарь пакетов и их версий
    """
    requirements = {}
    with open(requirements_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Пропускаем комментарии и пустые строки
            if not line or line.startswith("#"):
                continue

            # Убираем комментарии из строки
            if "#" in line:
                line = line.split("#")[0].strip()

            # Парсим пакет и версию
            # Поддерживаем форматы: package==version, package[extra]==version
            if "==" in line:
                # Обработка package[extra]==version
                if "[" in line and "]" in line:
                    match = re.match(r"([^[]+)\[.*?\]==(.+)", line)
                    if match:
                        package = match.group(1).strip()
                        version_str = match.group(2).strip()
                        requirements[package.lower()] = version_str
                else:
                    parts = line.split("==")
                    if len(parts) == 2:
                        package = parts[0].strip()
                        version_str = parts[1].strip()
                        requirements[package.lower()] = version_str

    return requirements


def compare_versions(current: str, latest: str) -> str:
    """
    Сравнивает версии и возвращает статус.

    Args:
        current: Текущая версия
        latest: Последняя версия

    Returns:
        Статус: "up_to_date", "outdated", "newer", "error"
    """
    try:
        current_ver = version.parse(current)
        latest_ver = version.parse(latest)

        if current_ver == latest_ver:
            return "up_to_date"
        elif current_ver < latest_ver:
            return "outdated"
        else:
            return "newer"
    except Exception:
        return "error"


def main():
    """Основная функция проверки версий."""
    print("=" * 80)
    print("Проверка актуальности версий пакетов в requirements.txt")
    print("=" * 80)

    requirements_file = root_dir / "requirements.txt"
    if not requirements_file.exists():
        print(f"[ERROR] Файл {requirements_file} не найден")
        return 1

    # Парсим requirements.txt
    print("\n[INFO] Парсинг requirements.txt...")
    requirements = parse_requirements(requirements_file)
    print(f"[OK] Найдено пакетов: {len(requirements)}")

    # Проверяем версии
    print("\n[INFO] Проверка версий на PyPI...")
    print("Это может занять некоторое время...\n")

    results = {
        "up_to_date": [],
        "outdated": [],
        "newer": [],
        "not_found": [],
        "errors": [],
    }

    total = len(requirements)
    current = 0

    for package_name, current_version in sorted(requirements.items()):
        current += 1
        print(f"[{current}/{total}] Проверка {package_name}=={current_version}...", end=" ")

        latest_version, success = get_latest_version(package_name)

        if not success:
            results["errors"].append((package_name, current_version, latest_version))
            print(f"[ERROR] {latest_version}")
            continue

        # Проверяем, существует ли указанная версия
        try:
            # Пытаемся получить информацию о конкретной версии
            url = f"https://pypi.org/pypi/{package_name}/{current_version}/json"
            response = requests.get(url, timeout=5)
            version_exists = response.status_code == 200
        except Exception:
            version_exists = False

        if not version_exists:
            results["not_found"].append((package_name, current_version, latest_version))
            print(f"[NOT FOUND] Версия {current_version} не существует! Последняя: {latest_version}")
            continue

        status = compare_versions(current_version, latest_version)

        if status == "up_to_date":
            results["up_to_date"].append((package_name, current_version, latest_version))
            print(f"[OK] Актуальна ({latest_version})")
        elif status == "outdated":
            results["outdated"].append((package_name, current_version, latest_version))
            print(f"[OUTDATED] Доступна {latest_version}")
        elif status == "newer":
            results["newer"].append((package_name, current_version, latest_version))
            print(f"[NEWER] Текущая {current_version} новее PyPI {latest_version} (возможно, dev версия)")
        else:
            results["errors"].append((package_name, current_version, latest_version))
            print(f"[ERROR] Ошибка сравнения версий")

    # Итоговый отчет
    print("\n" + "=" * 80)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 80)

    print(f"\n✅ Актуальные версии: {len(results['up_to_date'])}")
    if results["up_to_date"]:
        for pkg, curr, latest in results["up_to_date"][:10]:  # Показываем первые 10
            print(f"   {pkg}=={curr}")

    print(f"\n⚠️  Устаревшие версии: {len(results['outdated'])}")
    if results["outdated"]:
        for pkg, curr, latest in results["outdated"]:
            print(f"   {pkg}: {curr} → {latest}")

    print(f"\n❌ Версии не найдены на PyPI: {len(results['not_found'])}")
    if results["not_found"]:
        for pkg, curr, latest in results["not_found"]:
            print(f"   {pkg}=={curr} (не существует, последняя: {latest})")

    print(f"\n🔴 Ошибки при проверке: {len(results['errors'])}")
    if results["errors"]:
        for pkg, curr, error in results["errors"]:
            print(f"   {pkg}=={curr}: {error}")

    print(f"\n📊 Статистика:")
    print(f"   Всего пакетов: {total}")
    print(f"   Актуальных: {len(results['up_to_date'])} ({len(results['up_to_date'])/total*100:.1f}%)")
    print(f"   Устаревших: {len(results['outdated'])} ({len(results['outdated'])/total*100:.1f}%)")
    print(f"   Не найдено: {len(results['not_found'])} ({len(results['not_found'])/total*100:.1f}%)")

    # Сохраняем отчет в файл
    report_file = root_dir / "dependency_version_report.json"
    report_data = {
        "summary": {
            "total": total,
            "up_to_date": len(results["up_to_date"]),
            "outdated": len(results["outdated"]),
            "not_found": len(results["not_found"]),
            "errors": len(results["errors"]),
        },
        "details": {
            "up_to_date": [{"package": p, "version": v, "latest": l} for p, v, l in results["up_to_date"]],
            "outdated": [{"package": p, "current": v, "latest": l} for p, v, l in results["outdated"]],
            "not_found": [{"package": p, "current": v, "latest": l} for p, v, l in results["not_found"]],
            "errors": [{"package": p, "current": v, "error": str(e)} for p, v, e in results["errors"]],
        },
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"\n[INFO] Отчет сохранен в {report_file}")

    # Возвращаем код ошибки, если есть проблемы
    if results["not_found"] or results["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

