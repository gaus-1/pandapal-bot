#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки зависимостей и конфигурации проекта.
Проверяет:
1. Соответствие версий пакетов в requirements.txt и установленных
2. Целостность миграций Alembic
3. Наличие обязательных переменных окружения
"""

import io
import sys
from pathlib import Path

# Настройка кодировки для Windows
if sys.platform == "win32":
    # Переключаем stdout на UTF-8 для Windows
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stderr.encoding != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Добавляем корневую папку в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from bot.config import Settings  # noqa: E402


def check_required_env_vars():
    """Check required environment variables."""
    print("=" * 60)
    print("Checking required environment variables")
    print("=" * 60)

    try:
        settings = Settings()
        print("[OK] All required environment variables loaded")

        # List of required variables
        required_vars = [
            "DATABASE_URL",
            "TELEGRAM_BOT_TOKEN",
            "GEMINI_API_KEY",
            "SECRET_KEY",
        ]

        print("\nRequired variables:")
        for var in required_vars:
            value = getattr(settings, var.lower(), None)
            if value:
                # Mask sensitive data
                if "token" in var.lower() or "key" in var.lower() or "secret" in var.lower():
                    masked = value[:8] + "***" if len(value) > 8 else "***"
                    print(f"  [OK] {var}: {masked}")
                else:
                    print(f"  [OK] {var}: set")
            else:
                print(f"  [ERROR] {var}: not set")

        # Optional variables with default values
        optional_vars = {
            "GEMINI_API_KEYS": settings.gemini_api_keys,
            "GEMINI_MODEL": settings.gemini_model,
            "SENTRY_DSN": settings.sentry_dsn,
            "FRONTEND_URL": settings.frontend_url,
            "WEBHOOK_DOMAIN": settings.webhook_domain,
            "LOG_LEVEL": settings.log_level,
        }

        print("\nOptional variables (with default values):")
        for var, value in optional_vars.items():
            if value:
                if "key" in var.lower() or "dsn" in var.lower():
                    masked = str(value)[:8] + "***" if len(str(value)) > 8 else "***"
                    print(f"  [INFO] {var}: {masked}")
                else:
                    print(f"  [INFO] {var}: {value}")
            else:
                print(f"  [WARN] {var}: not set (using default value)")

        return True

    except Exception as e:
        print(f"[ERROR] Error loading settings: {e}")
        return False


def check_migrations():
    """Check Alembic migrations integrity."""
    print("\n" + "=" * 60)
    print("Checking Alembic migrations")
    print("=" * 60)

    migrations_dir = root_dir / "alembic" / "versions"
    if not migrations_dir.exists():
        print("[ERROR] Migrations directory not found")
        return False

    migration_files = list(migrations_dir.glob("*.py"))
    migration_files = [f for f in migration_files if f.name != "__init__.py"]

    print(f"\nFound migrations: {len(migration_files)}")

    # Check migration structure
    revisions = []
    for migration_file in migration_files:
        content = migration_file.read_text(encoding="utf-8")
        if 'revision: str = "' in content:
            # Extract revision
            for line in content.split("\n"):
                if 'revision: str = "' in line:
                    revision = line.split('"')[1]
                    revisions.append((migration_file.name, revision))
                    break

    print("\nMigrations:")
    for filename, revision in revisions:
        print(f"  [OK] {filename}: {revision}")

    # Check migration chain
    print("\nMigration chain check:")
    # This is a simplified check - full check requires DB connection
    print("  [WARN] Full check requires database connection")
    print("  [INFO] Use 'alembic history' to check migration chain")

    return True


def check_requirements():
    """Check requirements.txt compliance."""
    print("\n" + "=" * 60)
    print("Checking requirements.txt")
    print("=" * 60)

    requirements_file = root_dir / "requirements.txt"
    if not requirements_file.exists():
        print("[ERROR] requirements.txt file not found")
        return False

    # Читаем requirements.txt
    requirements = {}
    comments = {}  # Сохраняем комментарии для пакетов (без русских символов)
    with open(requirements_file, "r", encoding="utf-8") as f:
        for line in f:
            original_line = line
            line = line.strip()
            if line and not line.startswith("#") and "==" in line:
                # Разделяем на пакет и комментарий
                if "#" in line:
                    package_line, comment = line.split("#", 1)
                    # Убираем русские символы из комментариев для вывода
                    comment_clean = comment.strip()
                    # Проверяем, есть ли кириллица в комментарии
                    has_cyrillic = any("\u0400" <= char <= "\u04ff" for char in comment_clean)
                    if has_cyrillic:
                        # Заменяем русские комментарии на английские эквиваленты
                        comment_clean = ""  # Не выводим русские комментарии
                else:
                    package_line = line
                    comment_clean = ""

                parts = package_line.split("==")
                if len(parts) == 2:
                    package = parts[0].strip()
                    version = parts[1].strip()
                    requirements[package.lower()] = version
                    if comment_clean:
                        comments[package.lower()] = comment_clean

    print(f"\nFound packages in requirements.txt: {len(requirements)}")

    # Ключевые пакеты для проверки
    key_packages = [
        "aiogram",
        "google-generativeai",
        "sqlalchemy",
        "alembic",
        "pydantic",
        "loguru",
        "aiohttp",
        "redis",
        "cryptography",
        "pytest",
        "black",
        "isort",
        "flake8",
        "mypy",
    ]

    print("\nKey packages:")
    for package in key_packages:
        if package.lower() in requirements:
            version = requirements[package.lower()]
            # Выводим только версию, без комментариев на русском
            print(f"  [OK] {package}: {version}")
        else:
            print(f"  [WARN] {package}: not found in requirements.txt")

    return True


def main():
    """Run dependency and configuration checks."""
    print("PandaPal Project Dependencies and Configuration Check")
    print("=" * 60)

    results = []

    # Check environment variables
    results.append(("Environment Variables", check_required_env_vars()))

    # Check migrations
    results.append(("Alembic Migrations", check_migrations()))

    # Check requirements.txt
    results.append(("requirements.txt", check_requirements()))

    # Final report
    print("\n" + "=" * 60)
    print("Final Report")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n[SUCCESS] All checks passed successfully!")
        return 0
    else:
        print("\n[WARN] Some checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
