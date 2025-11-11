#!/usr/bin/env python3
"""
🛡️ СКРИПТ ПРОВЕРКИ БЕЗОПАСНОСТИ
Автоматическая проверка на утечки секретных данных
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


class SecurityChecker:
    """🛡️ Проверка безопасности кода"""

    def __init__(self):
        self.sensitive_patterns = {
            # API ключи и токены
            "api_key": r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            "token": r'(?i)(token|access[_-]?token)\s*[=:]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?',
            "secret_key": r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?',
            # Пароли
            "password": r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^"\'\s]{8,})["\']?',
            "database_url": r'(?i)(database[_-]?url|db[_-]?url)\s*[=:]\s*["\']?(postgresql://[^"\'\s]+)["\']?',
            # Криптографические ключи
            "private_key": r'(?i)(private[_-]?key|privkey)\s*[=:]\s*["\']?(-----BEGIN[^"\']+-----END[^"\']+)["\']?',
            "certificate": r'(?i)(certificate|cert)\s*[=:]\s*["\']?(-----BEGIN[^"\']+-----END[^"\']+)["\']?',
            # Конкретные сервисы
            "telegram_token": r'telegram[_-]?bot[_-]?token\s*[=:]\s*["\']?(\d+:[a-zA-Z0-9_\-]{35})["\']?',
            "gemini_key": r'gemini[_-]?api[_-]?key\s*[=:]\s*["\']?(AIza[a-zA-Z0-9_\-]{35})["\']?',
            "openai_key": r'openai[_-]?api[_-]?key\s*[=:]\s*["\']?(sk-[a-zA-Z0-9_\-]{48})["\']?',
        }

        self.excluded_files = {
            ".git",
            ".gitignore",
            "node_modules",
            "__pycache__",
            ".env",
            ".env.example",
            "env.template",
            ".venv",
            "venv",
            "*.pyc",
            "*.log",
            "*.tmp",
            "*.bak",
            "dist",
            "build",
        }

        # Исключаем ложные срабатывания
        self.safe_patterns = [
            "settings.telegram_bot_token",  # Переменная окружения
            "YOUR_TELEGRAM_BOT_TOKEN",  # Шаблон
            "test_token",  # Тестовый токен
            "your_telegram_bot_token",  # Шаблон
        ]

        self.excluded_extensions = {".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".log"}

        self.violations: List[Dict] = []

    def should_skip_file(self, file_path: Path) -> bool:
        """Проверка, нужно ли пропустить файл"""
        # Проверяем расширение
        if file_path.suffix.lower() in self.excluded_extensions:
            return True

        # Проверяем имя файла
        for pattern in self.excluded_files:
            if file_path.name == pattern or file_path.name.endswith(pattern.replace("*", "")):
                return True

        # Проверяем путь
        for part in file_path.parts:
            if part in self.excluded_files:
                return True

        return False

    def check_file(self, file_path: Path) -> List[Dict]:
        """Проверка одного файла"""
        violations = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                # Пропускаем безопасные паттерны
                is_safe = any(safe_pattern in line for safe_pattern in self.safe_patterns)
                if is_safe:
                    continue

                for pattern_name, pattern in self.sensitive_patterns.items():
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        violation = {
                            "file": str(file_path),
                            "line": line_num,
                            "pattern": pattern_name,
                            "content": line.strip(),
                            "match": match.group(0) if match.groups() else match.group(0),
                        }
                        violations.append(violation)

        except Exception as e:
            print(f"⚠️ Ошибка чтения файла {file_path}: {e}")

        return violations

    def scan_directory(self, directory: Path) -> List[Dict]:
        """Сканирование директории"""
        all_violations = []

        for file_path in directory.rglob("*"):
            if file_path.is_file() and not self.should_skip_file(file_path):
                violations = self.check_file(file_path)
                all_violations.extend(violations)

        return all_violations

    def generate_report(self, violations: List[Dict]) -> str:
        """Генерация отчета"""
        if not violations:
            return "✅ ПРОВЕРКА БЕЗОПАСНОСТИ ПРОЙДЕНА!\nНикаких утечек секретных данных не найдено."

        report = f"🚨 НАЙДЕНО {len(violations)} НАРУШЕНИЙ БЕЗОПАСНОСТИ!\n\n"

        # Группируем по файлам
        by_file = {}
        for violation in violations:
            file_name = violation["file"]
            if file_name not in by_file:
                by_file[file_name] = []
            by_file[file_name].append(violation)

        for file_name, file_violations in by_file.items():
            report += f"📄 {file_name}:\n"
            for violation in file_violations:
                report += f"  ❌ Строка {violation['line']}: {violation['pattern']}\n"
                report += f"     {violation['content'][:100]}...\n\n"

        return report

    def run_check(self, directory: str = ".") -> bool:
        """Запуск проверки"""
        print("🛡️ Запуск проверки безопасности...")

        directory_path = Path(directory)
        if not directory_path.exists():
            print(f"❌ Директория {directory} не существует")
            return False

        violations = self.scan_directory(directory_path)
        self.violations = violations

        report = self.generate_report(violations)
        print(report)

        return len(violations) == 0


def main():
    """Главная функция"""
    checker = SecurityChecker()

    # Проверяем текущую директорию
    success = checker.run_check(".")

    if success:
        print("\n✅ Все проверки безопасности пройдены успешно!")
        sys.exit(0)
    else:
        print("\n❌ Обнаружены нарушения безопасности!")
        print("🔧 Исправьте найденные проблемы перед коммитом.")
        sys.exit(1)


if __name__ == "__main__":
    main()
