#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для оптимизации критичных конфигурационных файлов для продакшена.

Этот скрипт создает оптимизированные версии конфигурационных файлов
для использования в продакшене. Оригинальные файлы остаются для разработки.
"""

import os
import shutil
from pathlib import Path

# Корневая директория проекта
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "bot" / "config"
OPTIMIZED_DIR = CONFIG_DIR / "_obfuscated"  # Директория для оптимизированных версий

# Файлы для оптимизации
FILES_TO_OPTIMIZE = [
    "prompts.py",
    "forbidden_patterns.py",
]


def optimize_files():
    """Оптимизировать указанные файлы для продакшена."""
    print("[OPTIMIZE] Starting optimization of critical config files...")

    # Создаем директорию для оптимизированных файлов
    OPTIMIZED_DIR.mkdir(exist_ok=True)

    # Оптимизируем каждый файл
    for filename in FILES_TO_OPTIMIZE:
        source_file = CONFIG_DIR / filename
        if not source_file.exists():
            print(f"[WARNING] File not found: {source_file}")
            continue

        print(f"[OPTIMIZE] Processing: {filename}")

        # Команда для оптимизации (использует PyArmor для защиты кода)
        # Режим restrict обеспечивает максимальную защиту
        cmd = f'pyarmor gen --restrict --output "{OPTIMIZED_DIR}" "{source_file}"'
        result = os.system(cmd)

        # Проверяем результат
        optimized_file = OPTIMIZED_DIR / filename
        if optimized_file.exists() and result == 0:
            print(f"[SUCCESS] File optimized: {filename}")
        else:
            print(f"[ERROR] Failed to optimize: {filename}")

    print("[SUCCESS] Optimization completed!")
    print(f"[INFO] Optimized files in: {OPTIMIZED_DIR}")


if __name__ == "__main__":
    optimize_files()
