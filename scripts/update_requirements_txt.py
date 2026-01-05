#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для обновления requirements.txt с актуальными версиями.
"""

import re
from pathlib import Path

# Словарь обновлений: имя_пакета -> новая_версия
UPDATES = {
    # Приоритет 1 - Критичные
    "protobuf": "6.33.2",
    "pydantic": "2.12.5",
    "pydantic-settings": "2.12.0",
    "pydantic_core": "2.41.5",
    "sentry-sdk": "2.48.0",
    # Приоритет 2 - Важные
    "SQLAlchemy": "2.0.45",
    "alembic": "1.17.2",
    "psycopg": "3.3.2",
    "psycopg-binary": "3.3.2",
    "fastapi": "0.125.0",
    "uvicorn": "0.38.0",
    "starlette": "0.50.0",
    # Google AI
    "google-generativeai": "0.8.6",
    "google-ai-generativelanguage": "0.9.0",
    "google-api-core": "2.28.1",
    "google-api-python-client": "2.187.0",
    "google-auth": "2.45.0",
    "google-auth-httplib2": "0.3.0",
    "googleapis-common-protos": "1.72.0",
    # gRPC
    "grpcio": "1.76.0",
    "grpcio-status": "1.76.0",
    "proto-plus": "1.27.0",
    # Telegram
    "aiogram": "3.23.0",
    # HTTP клиенты
    "aiohttp": "3.13.2",
    "aiofiles": "25.1.0",
    "urllib3": "2.6.2",
    "certifi": "2025.11.12",
    "idna": "3.11",
    "charset-normalizer": "3.4.4",
    # Утилиты
    "click": "8.3.1",
    "attrs": "25.4.0",
    "anyio": "4.12.0",
    "coverage": "7.13.0",
    "filelock": "3.20.1",
    "fsspec": "2025.12.0",
    "greenlet": "3.3.0",
    "joblib": "1.5.3",
    "multidict": "6.7.0",
    "platformdirs": "4.5.1",
    "typer": "0.20.1",
    "yarl": "1.22.0",
    "tzdata": "2025.3",
    "virtualenv": "20.35.4",
    "python-dotenv": "1.2.1",
    # Парсинг
    "beautifulsoup4": "4.14.3",
    "soupsieve": "2.8.1",
    "ruamel.yaml": "0.18.17",
    "ruamel.yaml.clib": "0.2.15",
    # Безопасность
    "safety": "3.7.0",
    "safety-schemas": "0.0.17",
    "bandit": "1.9.2",
    "authlib": "1.6.6",
    # Инструменты разработки
    "cfgv": "3.5.0",
    "iniconfig": "2.3.0",
    "pylint": "4.0.4",
    "marshmallow": "4.1.1",
    "cachetools": "6.2.4",
    "propcache": "0.4.1",
    "pytokens": "0.3.0",
    "regex": "2025.11.3",
    "qrcode": "8.2",
    "networkx": "3.6.1",
    "nodeenv": "1.10.0",
    "pre_commit": "4.5.1",
    "faker": "39.0.0",
    "fakeredis": "2.33.0",
    "black": "25.12.0",
    "mypy": "1.19.1",
    "pytest-asyncio": "1.3.0",
    "numpy": "2.3.5",
    # Исправление
    "frozenlist": "1.8.0",
}


def update_requirements():
    """Обновить requirements.txt."""
    requirements_file = Path("requirements.txt")

    if not requirements_file.exists():
        print("[ERROR] requirements.txt не найден")
        return False

    content = requirements_file.read_text(encoding="utf-8")
    lines = content.split("\n")
    updated_lines = []
    updated_count = 0

    for line in lines:
        original_line = line
        stripped = line.strip()

        # Пропускаем комментарии и пустые строки
        if not stripped or stripped.startswith("#"):
            updated_lines.append(line)
            continue

        # Убираем комментарии из строки для парсинга
        if "#" in stripped:
            package_part = stripped.split("#")[0].strip()
            comment_part = " #" + stripped.split("#", 1)[1]
        else:
            package_part = stripped
            comment_part = ""

        # Парсим пакет и версию
        if "==" in package_part:
            # Обработка package[extra]==version
            if "[" in package_part and "]" in package_part:
                match = re.match(r"([^[]+)\[.*?\]==(.+)", package_part)
                if match:
                    package_name = match.group(1).strip()
                    old_version = match.group(2).strip()
                    extra = package_part[package_part.find("[") : package_part.find("]") + 1]

                    if package_name.lower() in UPDATES:
                        new_version = UPDATES[package_name.lower()]
                        new_line = f"{package_name}{extra}=={new_version}{comment_part}"
                        updated_lines.append(new_line)
                        updated_count += 1
                        print(f"[OK] {package_name}: {old_version} → {new_version}")
                    else:
                        updated_lines.append(line)
            else:
                parts = package_part.split("==")
                if len(parts) == 2:
                    package_name = parts[0].strip()
                    old_version = parts[1].strip()

                    if package_name.lower() in UPDATES:
                        new_version = UPDATES[package_name.lower()]
                        new_line = f"{package_name}=={new_version}{comment_part}"
                        updated_lines.append(new_line)
                        updated_count += 1
                        print(f"[OK] {package_name}: {old_version} → {new_version}")
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Сохраняем обновленный файл
    new_content = "\n".join(updated_lines)
    requirements_file.write_text(new_content, encoding="utf-8")

    print(f"\n[SUCCESS] Обновлено {updated_count} пакетов в requirements.txt")
    return True


if __name__ == "__main__":
    print("Обновление requirements.txt с актуальными версиями...")
    update_requirements()
