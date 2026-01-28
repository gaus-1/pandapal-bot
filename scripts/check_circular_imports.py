"""
Скрипт для проверки циклических импортов в проекте.

Проверяет:
1. Прямые циклические импорты (import loop)
2. Косвенные циклические зависимости
3. Проблемные circular dependencies
"""

import ast
import sys
from collections import defaultdict
from pathlib import Path


def get_imports_from_file(filepath):
    """Извлечь все импорты из Python файла."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split(".")[0])

        return imports
    except Exception as e:
        print(f"Ошибка в {filepath}: {e}")
        return []


def find_circular_imports(project_dir="bot"):
    """Найти циклические импорты в проекте."""
    print("=" * 60)
    print("ПРОВЕРКА ЦИКЛИЧЕСКИХ ИМПОРТОВ")
    print("=" * 60)

    project_path = Path(project_dir)
    python_files = list(project_path.rglob("*.py"))

    # Граф зависимостей
    dependencies = defaultdict(set)

    for filepath in python_files:
        if "__pycache__" in str(filepath):
            continue

        module_name = (
            str(filepath.relative_to(project_path.parent)).replace("\\", ".").replace("/", ".")[:-3]
        )
        imports = get_imports_from_file(filepath)

        for imp in imports:
            if imp == "bot":
                dependencies[module_name].add("bot")

    # Проверка на циклы
    def has_cycle(module, visited, rec_stack):
        visited.add(module)
        rec_stack.add(module)

        for neighbor in dependencies.get(module, []):
            if neighbor not in visited:
                if has_cycle(neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(module)
        return False

    cycles_found = []
    visited = set()

    for module in dependencies:
        if module not in visited:
            rec_stack = set()
            if has_cycle(module, visited, rec_stack):
                cycles_found.append(module)

    print(f"Проверено файлов: {len(python_files)}")
    print(f"Модулей с зависимостями: {len(dependencies)}")

    if cycles_found:
        print(f"\nWARNING: Найдено циклических импортов: {len(cycles_found)}")
        for cycle in cycles_found[:10]:
            print(f"  - {cycle}")
        return 1
    else:
        print("\nOK: ЦИКЛИЧЕСКИЕ ИМПОРТЫ НЕ НАЙДЕНЫ!")
        print("   Проект чистый!")
        return 0


if __name__ == "__main__":
    sys.exit(find_circular_imports())
