"""
Скрипт для исправления кодировки русских комментариев в Python файлах.
Конвертирует все файлы в UTF-8.
"""

import os
import sys


def fix_encoding(directory="."):
    """Исправить кодировку файлов в указанной директории."""
    fixed_count = 0
    error_count = 0

    # Рекурсивно проходим по всем Python файлам
    for root, dirs, files in os.walk(directory):
        # Пропускаем виртуальное окружение и .git
        if any(skip in root for skip in ["venv", ".git", "__pycache__", "node_modules"]):
            continue

        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            try:
                # Читаем файл в бинарном режиме
                with open(filepath, "rb") as f:
                    content_bytes = f.read()

                # Пытаемся декодировать с разными кодировками
                content = None
                for encoding in ["utf-8", "cp1251", "windows-1251", "latin-1"]:
                    try:
                        content = content_bytes.decode(encoding)
                        # Проверяем, есть ли русские буквы
                        if any(ord(c) > 127 for c in content):
                            break
                    except:
                        continue

                if content is None:
                    print(f"ERROR: {filepath} - ne udalos dekodirovat")
                    error_count += 1
                    continue

                # Перезаписываем файл в UTF-8
                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    f.write(content)

                fixed_count += 1
                if fixed_count % 10 == 0:
                    print(f"OK: Obrabotano {fixed_count} faylov...")

            except Exception as e:
                print(f"ERROR: {filepath} - {e}")
                error_count += 1

    return fixed_count, error_count


if __name__ == "__main__":
    print("Ispravlenie kodirovki faylov proekta...")
    print("=" * 60)

    fixed, errors = fix_encoding()

    print("=" * 60)
    print(f"Uspeshno obrabotano: {fixed} faylov")
    print(f"Oshibok: {errors} faylov")
    print("Gotovo!")
