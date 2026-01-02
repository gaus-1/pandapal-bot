#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для обфускации критичных конфигурационных файлов.

ВАЖНО: Этот скрипт используется для защиты интеллектуальной собственности.
Обфусцированные файлы заменяют оригинальные в продакшене.
"""

import os
import shutil
from pathlib import Path

# Корневая директория проекта
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "bot" / "config"
OBFUSCATED_DIR = CONFIG_DIR / "_obfuscated"

# Файлы для обфускации
FILES_TO_OBFUSCATE = [
    "prompts.py",
    "forbidden_patterns.py",
]


def obfuscate_files():
    """Обфусцировать указанные файлы."""
    print("[OBFUSCATE] Starting obfuscation of critical files...")

    # Создаем директорию для обфусцированных файлов
    OBFUSCATED_DIR.mkdir(exist_ok=True)

    # Обфусцируем каждый файл
    for filename in FILES_TO_OBFUSCATE:
        source_file = CONFIG_DIR / filename
        if not source_file.exists():
            print(f"[WARNING] File not found: {source_file}")
            continue

        print(f"[OBFUSCATE] Processing: {filename}")

        # PyArmor команда для обфускации
        # Используем режим restrict для максимальной защиты
        cmd = f'pyarmor gen --restrict --output "{OBFUSCATED_DIR}" "{source_file}"'
        result = os.system(cmd)

        # Проверяем результат
        obfuscated_file = OBFUSCATED_DIR / filename
        if obfuscated_file.exists() and result == 0:
            print(f"[SUCCESS] File obfuscated: {filename}")
        else:
            print(f"[ERROR] Failed to obfuscate: {filename}")

    print("[SUCCESS] Obfuscation completed!")
    print(f"[INFO] Obfuscated files in: {OBFUSCATED_DIR}")


if __name__ == "__main__":
    obfuscate_files()
