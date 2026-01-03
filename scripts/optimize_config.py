#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для оптимизации критичных конфигурационных файлов для продакшена.

Этот скрипт создает оптимизированные версии конфигурационных файлов
для использования в продакшене. Оригинальные файлы остаются для разработки.
"""

import os
import re
import shutil
import sys
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


def post_process_obfuscated_file(file_path: Path):
    """Постобработка обфусцированного файла: удаление упоминаний PyArmor."""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Удаляем первую строку с комментарием PyArmor (регистронезависимо)
        if lines and (
            "# Pyarmor" in lines[0] or "# PyArmor" in lines[0] or "# pyarmor" in lines[0]
        ):
            lines = lines[1:]
            print(f"  [POST] Removed PyArmor comment from {file_path.name}")

        # Заменяем импорт pyarmor_runtime на нейтральное имя с относительным путем
        new_lines = []
        runtime_dir_old = None
        for line in lines:
            # Ищем импорт pyarmor_runtime
            match = re.search(r"from\s+(pyarmor_runtime_\w+)\s+import", line)
            if match:
                runtime_dir_old = match.group(1)
                # Заменяем на относительный импорт _runtime
                new_line = line.replace(runtime_dir_old, "._runtime")
                new_lines.append(new_line)
                print(f"  [POST] Replaced runtime import in {file_path.name}")
            elif re.search(r"from\s+_runtime\s+import", line):
                # Если уже есть импорт _runtime, делаем его относительным
                new_line = line.replace("from _runtime import", "from ._runtime import")
                new_lines.append(new_line)
                print(f"  [POST] Made runtime import relative in {file_path.name}")
            else:
                new_lines.append(line)

        # Сохраняем обработанный файл
        file_path.write_text("\n".join(new_lines), encoding="utf-8")

        return runtime_dir_old
    except Exception as e:
        print(f"  [WARNING] Post-processing failed for {file_path.name}: {e}")
        return None


def rename_runtime_directory(optimized_dir: Path, old_name: str):
    """Переименовывает директорию runtime в нейтральное имя."""
    if not old_name:
        return

    old_runtime_dir = optimized_dir / old_name
    new_runtime_dir = optimized_dir / "_runtime"

    if old_runtime_dir.exists():
        if new_runtime_dir.exists():
            # Если новая директория уже существует, удаляем старую
            try:
                shutil.rmtree(old_runtime_dir)
                print(f"  [POST] Removed old runtime directory: {old_name}")
            except Exception as e:
                print(f"  [WARNING] Failed to remove old runtime directory: {e}")
        else:
            # Переименовываем
            try:
                old_runtime_dir.rename(new_runtime_dir)
                print(f"  [POST] Renamed runtime directory: {old_name} -> _runtime")
            except Exception as e:
                print(f"  [WARNING] Failed to rename runtime directory: {e}")

    # Очищаем __init__.py в _runtime от упоминаний PyArmor
    runtime_init = new_runtime_dir / "__init__.py"
    if runtime_init.exists():
        try:
            content = runtime_init.read_text(encoding="utf-8")
            lines = content.split("\n")
            # Удаляем первую строку с комментарием PyArmor (регистронезависимо)
            if lines and (
                "# Pyarmor" in lines[0] or "# PyArmor" in lines[0] or "# pyarmor" in lines[0]
            ):
                lines = lines[1:]
            # Заменяем импорт pyarmor_runtime на _core
            new_lines = []
            for line in lines:
                if "from .pyarmor_runtime import" in line or "from pyarmor_runtime import" in line:
                    new_lines.append("from ._core import __pyarmor__")
                    print(
                        f"  [POST] Replaced pyarmor_runtime import with _core in _runtime/__init__.py"
                    )
                else:
                    new_lines.append(line)
            runtime_init.write_text("\n".join(new_lines), encoding="utf-8")
            print(f"  [POST] Cleaned _runtime/__init__.py")
        except Exception as e:
            print(f"  [WARNING] Failed to clean _runtime/__init__.py: {e}")

    # Переименовываем pyarmor_runtime.pyd в _core.pyd если есть
    old_pyd = new_runtime_dir / "pyarmor_runtime.pyd"
    new_pyd = new_runtime_dir / "_core.pyd"
    if old_pyd.exists() and not new_pyd.exists():
        try:
            old_pyd.rename(new_pyd)
            print(f"  [POST] Renamed pyarmor_runtime.pyd -> _core.pyd")
        except Exception as e:
            print(f"  [WARNING] Failed to rename .pyd file: {e}")

    # Также проверяем .so файлы для Linux
    old_so = new_runtime_dir / "pyarmor_runtime.so"
    new_so = new_runtime_dir / "_core.so"
    if old_so.exists() and not new_so.exists():
        try:
            old_so.rename(new_so)
            print(f"  [POST] Renamed pyarmor_runtime.so -> _core.so")
        except Exception as e:
            print(f"  [WARNING] Failed to rename .so file: {e}")


def optimize_files():
    """Оптимизировать указанные файлы для продакшена."""
    print("[OPTIMIZE] Starting optimization of critical config files...")

    # Создаем директорию для оптимизированных файлов
    OPTIMIZED_DIR.mkdir(exist_ok=True)

    # Оптимизируем все файлы одним вызовом PyArmor
    source_files = [CONFIG_DIR / f for f in FILES_TO_OPTIMIZE if (CONFIG_DIR / f).exists()]

    if not source_files:
        print("[WARNING] No source files found!")
        return

    print(f"[OPTIMIZE] Processing {len(source_files)} files...")

    # Команда для оптимизации всех файлов сразу
    # Не используем --restrict чтобы избежать проверки окружения на Railway
    files_str = " ".join(f'"{f}"' for f in source_files)
    cmd = f'pyarmor gen --output "{OPTIMIZED_DIR}" {files_str}'
    result = os.system(cmd)

    if result != 0:
        print(f"[ERROR] Optimization failed with exit code {result}")
        sys.exit(1)

    print(f"[SUCCESS] All files optimized")

    # Постобработка: удаляем упоминания PyArmor из всех файлов
    print("[POST] Starting post-processing to remove PyArmor references...")
    runtime_dirs_found = set()

    for filename in FILES_TO_OPTIMIZE:
        optimized_file = OPTIMIZED_DIR / filename
        if optimized_file.exists():
            runtime_dir = post_process_obfuscated_file(optimized_file)
            if runtime_dir:
                runtime_dirs_found.add(runtime_dir)

    # Переименовываем директории runtime (обрабатываем все найденные)
    for runtime_dir in runtime_dirs_found:
        rename_runtime_directory(OPTIMIZED_DIR, runtime_dir)

    # Также проверяем и обрабатываем все директории pyarmor_runtime_*
    for item in OPTIMIZED_DIR.iterdir():
        if item.is_dir() and item.name.startswith("pyarmor_runtime_"):
            rename_runtime_directory(OPTIMIZED_DIR, item.name)

    # Проверяем что все файлы созданы
    all_created = True
    for filename in FILES_TO_OPTIMIZE:
        optimized_file = OPTIMIZED_DIR / filename
        if not optimized_file.exists():
            print(f"[ERROR] Optimized file not found: {optimized_file}")
            all_created = False

    if not all_created:
        print("[ERROR] Not all files were optimized successfully!")
        sys.exit(1)

    # Создаем __init__.py для экспорта переменных
    init_file = OPTIMIZED_DIR / "__init__.py"
    init_content = '''"""
Оптимизированные модули конфигурации для продакшена.

Этот пакет содержит оптимизированные версии критичных конфигурационных файлов
для использования в продакшене. Оригинальные файлы остаются для разработки.
"""

# Импортируем оптимизированные модули
from bot.config._obfuscated.forbidden_patterns import FORBIDDEN_PATTERNS
from bot.config._obfuscated.prompts import AI_SYSTEM_PROMPT

__all__ = ["AI_SYSTEM_PROMPT", "FORBIDDEN_PATTERNS"]
'''
    init_file.write_text(init_content, encoding="utf-8")
    print(f"[SUCCESS] Created __init__.py in {OPTIMIZED_DIR}")

    print("[SUCCESS] Optimization completed!")
    print(f"[INFO] Optimized files in: {OPTIMIZED_DIR}")


if __name__ == "__main__":
    try:
        optimize_files()
        print("[SUCCESS] All optimization completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Optimization failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
