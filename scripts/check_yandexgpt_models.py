"""
Скрипт для проверки доступности моделей YandexGPT в каталоге.
Проверяет, какие модели доступны для использования через API.
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from loguru import logger

from bot.config import settings


async def check_model_availability(model_name: str) -> bool:
    """
    Проверить доступность модели через тестовый запрос.

    Args:
        model_name: Название модели (например, yandexgpt-5.1-pro)

    Returns:
        bool: True если модель доступна, False если нет
    """
    api_key = settings.yandex_cloud_api_key
    folder_id = settings.yandex_cloud_folder_id
    gpt_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json",
    }

    # Минимальный тестовый запрос
    # Формат modelUri: gpt://folder_id/model_name
    # Если model_name уже содержит /latest или /rc, не добавляем их снова
    model_uri = f"gpt://{folder_id}/{model_name}"
    payload = {
        "modelUri": model_uri,
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": "10",  # Минимальное количество токенов для теста
        },
        "messages": [{"role": "user", "text": "Привет"}],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(gpt_url, headers=headers, json=payload)

            if response.status_code == 200:
                logger.info(f"✅ Модель {model_name} доступна")
                return True
            elif response.status_code == 404:
                logger.warning(f"❌ Модель {model_name} не найдена (404)")
                return False
            elif response.status_code == 403:
                logger.warning(f"⚠️ Модель {model_name} недоступна: нет доступа (403)")
                return False
            elif response.status_code == 500:
                logger.warning(
                    f"⚠️ Модель {model_name} вернула ошибку 500 (возможно, проблема на стороне Yandex Cloud)"
                )
                # HTTP 500 может означать, что модель подключена, но есть временная проблема
                return True
            else:
                logger.error(f"❌ Модель {model_name} вернула ошибку {response.status_code}")
                logger.error(f"Response: {response.text[:200]}")
                return False

    except Exception as e:
        logger.error(f"❌ Ошибка при проверке модели {model_name}: {e}")
        return False


async def main():
    """Проверить доступность различных моделей YandexGPT."""
    logger.info("🔍 Проверка доступности моделей YandexGPT в каталоге...")
    logger.info(f"📁 Folder ID: {settings.yandex_cloud_folder_id}")

    # Список моделей для проверки (разные форматы из документации Yandex Cloud)
    models_to_check = [
        # Стандартные модели (как в документации)
        "yandexgpt/latest",  # Последняя стабильная версия (используется сейчас)
        "yandexgpt/rc",  # Release candidate
        # Альтернативные форматы (могут быть доступны)
        "yandexgpt-pro",
        "yandexgpt-lite",
        "yandexgpt-5-pro",
        "yandexgpt-5.1-pro",
        "yandexgpt-5-lite",
    ]

    results = {}
    for model_name in models_to_check:
        logger.info(f"\n📋 Проверка модели: {model_name}")
        is_available = await check_model_availability(model_name)
        results[model_name] = is_available

    # Итоги
    logger.info("\n" + "=" * 60)
    logger.info("📊 ИТОГИ ПРОВЕРКИ:")
    logger.info("=" * 60)

    available_models = [model for model, available in results.items() if available]
    unavailable_models = [model for model, available in results.items() if not available]

    if available_models:
        logger.info(f"\n✅ Доступные модели ({len(available_models)}):")
        for model in available_models:
            logger.info(f"   - {model}")

    if unavailable_models:
        logger.info(f"\n❌ Недоступные модели ({len(unavailable_models)}):")
        for model in unavailable_models:
            logger.info(f"   - {model}")

    logger.info("\n" + "=" * 60)

    # Рекомендации
    if not available_models:
        logger.warning("⚠️ Ни одна модель не доступна!")
        logger.warning("   Проверьте:")
        logger.warning("   1. Правильность API ключа")
        logger.warning("   2. Права сервисного аккаунта (ai.languageModels.user)")
        logger.warning("   3. Квоты в Yandex Cloud Console")
        logger.warning("   4. Активацию моделей для каталога")

    return 0 if available_models else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
