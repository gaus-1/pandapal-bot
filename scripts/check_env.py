#!/usr/bin/env python3
"""
Скрипт для проверки переменных окружения в Railway.
Проверяет наличие всех необходимых переменных и их корректность.
"""

import os
import sys
from typing import Dict, List, Tuple

# Обязательные переменные
REQUIRED_VARS = {
    "DATABASE_URL": "postgresql:// или postgresql+psycopg://",
    "TELEGRAM_BOT_TOKEN": "токен от @BotFather",
    "YANDEX_CLOUD_API_KEY": "API ключ Yandex Cloud",
    "YANDEX_CLOUD_FOLDER_ID": "Folder ID Yandex Cloud",
    "SECRET_KEY": "секретный ключ (минимум 16 символов)",
}

# Опциональные переменные с дефолтами
OPTIONAL_VARS = {
    "AUTO_MIGRATE": "true/false",
    "AI_TEMPERATURE": "0.0-1.0",
    "AI_MAX_TOKENS": "100-8192",
    "CONTENT_FILTER_LEVEL": "1-5",
    "WEBHOOK_DOMAIN": "домен Railway",
    "FRONTEND_URL": "URL фронтенда",
    "LOG_LEVEL": "DEBUG/INFO/WARNING/ERROR",
    "ENVIRONMENT": "development/test/production",
}

# Переменные для проверки значений
VALIDATION_RULES = {
    "AI_TEMPERATURE": lambda v: 0.0 <= float(v) <= 1.0,
    "AI_MAX_TOKENS": lambda v: 100 <= int(v) <= 8192,
    "CONTENT_FILTER_LEVEL": lambda v: 1 <= int(v) <= 5,
    "AUTO_MIGRATE": lambda v: v.lower() in ("true", "false"),
    "SECRET_KEY": lambda v: len(v) >= 16,
    "DATABASE_URL": lambda v: v.startswith(("postgresql://", "postgres://", "sqlite://")),
}


def check_required_vars() -> Tuple[bool, List[str]]:
    """Проверка обязательных переменных."""
    missing = []
    for var, description in REQUIRED_VARS.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"[X] {var} - {description}")
        else:
            # Проверка на placeholder значения
            if value in ("your_" + var.lower(), "test_key", "your_folder_id"):
                missing.append(f"⚠️ {var} - установлено placeholder значение")
            else:
                print(f"[OK] {var} - установлен")

    return len(missing) == 0, missing


def check_optional_vars() -> Tuple[bool, List[str]]:
    """Проверка опциональных переменных."""
    warnings = []
    for var, description in OPTIONAL_VARS.items():
        value = os.getenv(var)
        if not value:
            warnings.append(f"ℹ️ {var} - не установлен (будет использован дефолт)")
        else:
            print(f"[OK] {var} = {value}")

    return True, warnings


def validate_values() -> Tuple[bool, List[str]]:
    """Валидация значений переменных."""
    errors = []
    for var, validator in VALIDATION_RULES.items():
        value = os.getenv(var)
        if value:
            try:
                if not validator(value):
                    errors.append(f"[X] {var} = {value} - недопустимое значение")
                else:
                    print(f"[OK] {var} = {value} - валидно")
            except (ValueError, TypeError) as e:
                errors.append(f"[X] {var} = {value} - ошибка валидации: {e}")

    return len(errors) == 0, errors


def check_railway_specific() -> Tuple[bool, List[str]]:
    """Проверка Railway-специфичных переменных."""
    warnings = []

    # Проверка DATABASE_URL на Railway переменные
    db_url = os.getenv("DATABASE_URL", "")
    if "${{" in db_url:
        print("ℹ️ DATABASE_URL содержит Railway переменную - будет подставлена при запуске")
        if "Postgres" not in db_url:
            warnings.append("⚠️ DATABASE_URL: проверьте имя Postgres сервиса")

    # Проверка окружения
    env = os.getenv("ENVIRONMENT", "production")
    if env == "production":
        print("[OK] ENVIRONMENT = production")
    else:
        warnings.append(f"⚠️ ENVIRONMENT = {env} (ожидается production)")

    # Проверка AUTO_MIGRATE
    auto_migrate = os.getenv("AUTO_MIGRATE", "false").lower()
    if auto_migrate == "true":
        print("[OK] AUTO_MIGRATE = true - автоматические миграции включены")
    else:
        warnings.append(
            "ℹ️ AUTO_MIGRATE не установлен в true - миграции не будут применяться автоматически"
        )

    return True, warnings


def main():
    """Основная функция проверки."""
    # Устанавливаем UTF-8 для Windows
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("Проверка переменных окружения...\n")

    # Проверка обязательных переменных
    print("📋 Обязательные переменные:")
    required_ok, required_errors = check_required_vars()
    print()

    # Проверка опциональных переменных
    print("📋 Опциональные переменные:")
    optional_ok, optional_warnings = check_optional_vars()
    print()

    # Валидация значений
    print("🔍 Валидация значений:")
    validation_ok, validation_errors = validate_values()
    print()

    # Railway-специфичные проверки
    print("🚂 Railway-специфичные проверки:")
    railway_ok, railway_warnings = check_railway_specific()
    print()

    # Итоги
    print("=" * 60)
    if required_ok and validation_ok:
        print("[OK] Все обязательные переменные установлены и валидны")
    else:
        print("[X] Обнаружены проблемы:")
        for error in required_errors + validation_errors:
            print(f"  {error}")

    if optional_warnings or railway_warnings:
        print("\n[!] Предупреждения:")
        for warning in optional_warnings + railway_warnings:
            print(f"  {warning}")

    print("=" * 60)

    # Возвращаем код выхода
    if required_ok and validation_ok:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
