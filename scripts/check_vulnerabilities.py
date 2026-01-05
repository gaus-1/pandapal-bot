"""
Скрипт для проверки уязвимостей в зависимостях проекта

Проверяет:
- Python зависимости (requirements.txt) через safety
- Node.js зависимости (package.json) через npm audit

Использование:
    python scripts/check_vulnerabilities.py
"""

import json
import subprocess
import sys
from pathlib import Path

from loguru import logger


def check_python_vulnerabilities():
    """Проверка уязвимостей Python зависимостей через safety"""
    logger.info("🔍 Проверка уязвимостей Python зависимостей...")

    try:
        # Проверяем что safety установлен
        result = subprocess.run(
            ["safety", "check", "--json"], capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            logger.success("✅ Python зависимости безопасны")
            return True
        else:
            # Парсим JSON вывод
            try:
                vulnerabilities = json.loads(result.stdout)
                if vulnerabilities:
                    logger.error("❌ Найдены уязвимости в Python зависимостях:")
                    for vuln in vulnerabilities:
                        logger.error(
                            f"  - {vuln.get('package', 'unknown')}: {vuln.get('vulnerability', 'unknown')}"
                        )
                    return False
                else:
                    logger.success("✅ Python зависимости безопасны")
                    return True
            except json.JSONDecodeError:
                # Если не JSON, выводим текст
                logger.warning("⚠️ Не удалось распарсить вывод safety:")
                logger.warning(result.stdout)
                return False

    except FileNotFoundError:
        logger.warning("⚠️ safety не установлен. Установите: pip install safety")
        logger.info("💡 Пропускаем проверку Python зависимостей")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке Python зависимостей: {e}")
        return False


def check_nodejs_vulnerabilities():
    """Проверка уязвимостей Node.js зависимостей через npm audit"""
    logger.info("🔍 Проверка уязвимостей Node.js зависимостей...")

    frontend_dir = Path(__file__).parent.parent / "frontend"

    if not frontend_dir.exists():
        logger.warning("⚠️ Директория frontend не найдена")
        return None

    try:
        # Запускаем npm audit
        result = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            logger.success("✅ Node.js зависимости безопасны")
            return True
        else:
            # Парсим JSON вывод
            try:
                audit_data = json.loads(result.stdout)
                vulnerabilities = audit_data.get("vulnerabilities", {})

                if vulnerabilities:
                    logger.error("❌ Найдены уязвимости в Node.js зависимостях:")
                    for package, vuln_data in vulnerabilities.items():
                        severity = vuln_data.get("severity", "unknown")
                        logger.error(f"  - {package}: {severity}")
                    return False
                else:
                    logger.success("✅ Node.js зависимости безопасны")
                    return True
            except json.JSONDecodeError:
                # Если не JSON, выводим текст
                logger.warning("⚠️ Не удалось распарсить вывод npm audit:")
                logger.warning(result.stdout)
                return False

    except FileNotFoundError:
        logger.warning("⚠️ npm не установлен. Пропускаем проверку Node.js зависимостей")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке Node.js зависимостей: {e}")
        return False


def main():
    """Главная функция"""
    logger.info("🔒 Проверка уязвимостей зависимостей проекта PandaPal")

    python_result = check_python_vulnerabilities()
    nodejs_result = check_nodejs_vulnerabilities()

    # Определяем общий результат
    if python_result is False or nodejs_result is False:
        logger.error("❌ Обнаружены уязвимости! Исправьте их перед деплоем.")
        sys.exit(1)
    elif python_result is None and nodejs_result is None:
        logger.warning("⚠️ Не удалось проверить уязвимости (инструменты не установлены)")
        logger.info("💡 Установите: pip install safety")
        sys.exit(0)
    else:
        logger.success("✅ Все зависимости безопасны!")
        sys.exit(0)


if __name__ == "__main__":
    main()
