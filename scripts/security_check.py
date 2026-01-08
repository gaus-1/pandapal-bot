#!/usr/bin/env python3
"""
🛡️ СКРИПТ ПРОВЕРКИ БЕЗОПАСНОСТИ
Автоматическая проверка на утечки секретных данных
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List


class SecurityChecker:
    """🛡️ Проверка безопасности кода"""

    def __init__(self):
        self.sensitive_patterns = {
            # API ключи и токены
            "api_key": r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            "token": r'(?i)(token|access[_-]?token)\s*[=:]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?',
            "secret_key": r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-\.]{32,})["\']?',
            # Пароли
            "password": r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^"\'\s]{8,})["\']?',
            "database_url": r'(?i)(database[_-]?url|db[_-]?url)\s*[=:]\s*["\']?(postgresql://[^"\'\s]+)["\']?',
            # Криптографические ключи
            "private_key": r'(?i)(private[_-]?key|privkey)\s*[=:]\s*["\']?(-----BEGIN[^"\']+-----END[^"\']+)["\']?',
            "certificate": r'(?i)(certificate|cert)\s*[=:]\s*["\']?(-----BEGIN[^"\']+-----END[^"\']+)["\']?',
            # Конкретные сервисы
            "telegram_token": r'telegram[_-]?bot[_-]?token\s*[=:]\s*["\']?(\d+:[a-zA-Z0-9_\-]{35})["\']?',
            "yandex_api_key": r'yandex[_-]?cloud[_-]?api[_-]?key\s*[=:]\s*["\']?(AQVN[a-zA-Z0-9_\-]{35,})["\']?',
            "yookassa_secret": r'yookassa[_-]?secret[_-]?key\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{32,})["\']?',
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
            "settings.",  # Использование переменных окружения через settings
            "YOUR_",  # Шаблоны
            "test_",  # Тестовые значения
            "your_",  # Шаблоны
            "self.secret_key",  # Использование атрибутов класса
            "Configuration.secret_key",  # Использование конфигурации
            "base64.urlsafe_b64encode",  # Криптографические функции
            "Field(",  # Pydantic Field definitions
            "validation_alias",  # Pydantic validation
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
            return "OK: SECURITY CHECK PASSED!\nNo secret leaks found."

        report = f"FOUND {len(violations)} SECURITY VIOLATIONS!\n\n"

        # Группируем по файлам
        by_file = {}
        for violation in violations:
            file_name = violation["file"]
            if file_name not in by_file:
                by_file[file_name] = []
            by_file[file_name].append(violation)

        for file_name, file_violations in by_file.items():
            report += f"FILE: {file_name}\n"
            for violation in file_violations:
                report += f"  Line {violation['line']}: {violation['pattern']}\n"
                report += f"     {violation['content'][:100]}\n\n"

        return report

    def run_check(self, directories: List[str] = None) -> bool:
        """Запуск проверки"""
        if directories is None:
            directories = ["bot", "scripts", "web_server.py", "frontend_server.py"]

        try:
            print("Security check started...")
        except UnicodeEncodeError:
            print("Security check started...")

        all_violations = []
        for directory in directories:
            directory_path = Path(directory)
            if not directory_path.exists():
                print(f"WARNING: Directory {directory} does not exist, skipping")
                continue

            if directory_path.is_file():
                violations = self.check_file(directory_path)
            else:
                violations = self.scan_directory(directory_path)
            all_violations.extend(violations)

        self.violations = all_violations

        report = self.generate_report(all_violations)
        try:
            print(report)
        except UnicodeEncodeError:
            # Fallback без эмодзи для Windows
            report_clean = report.encode("ascii", "ignore").decode("ascii")
            print(report_clean)

        return len(all_violations) == 0


def main():
    """Главная функция"""
    checker = SecurityChecker()

    # Проверяем только нужные директории
    directories = ["bot", "scripts", "web_server.py", "frontend_server.py"]
    success = checker.run_check(directories)

    if success:
        try:
            print("\nOK: All security checks passed!")
        except UnicodeEncodeError:
            print("\nOK: All security checks passed!")
        sys.exit(0)
    else:
        try:
            print("\nERROR: Security violations found!")
            print("Fix the issues before committing.")
        except UnicodeEncodeError:
            print("\nERROR: Security violations found!")
            print("Fix the issues before committing.")
        sys.exit(1)


if __name__ == "__main__":
    main()
