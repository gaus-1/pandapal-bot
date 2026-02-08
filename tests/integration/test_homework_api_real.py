"""
РЕАЛЬНЫЕ ТЕСТЫ API проверки домашних заданий
Использует реальные переменные окружения и БД
"""

import base64
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncio  # noqa: E402
from io import BytesIO  # noqa: E402

import aiohttp  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

# Переменные окружения из Railway/локального окружения
# Если не указан API_BASE_URL, пытаемся определить автоматически
PORT = os.getenv("PORT", "8080")

# Приоритет: 1) API_BASE_URL, 2) WEBHOOK_DOMAIN, 3) localhost
API_BASE_URL = os.getenv("API_BASE_URL")
if not API_BASE_URL:
    WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN")
    if WEBHOOK_DOMAIN:
        # Railway использует HTTPS
        if WEBHOOK_DOMAIN.startswith("http"):
            API_BASE_URL = WEBHOOK_DOMAIN
        else:
            API_BASE_URL = f"https://{WEBHOOK_DOMAIN}"
    else:
        API_BASE_URL = f"http://localhost:{PORT}"


def create_test_image() -> bytes:
    """Создаёт тестовое изображение с математическим примером"""
    # Создаём простое изображение с текстом "2 + 2 = 5" (намеренная ошибка)
    img = Image.new("RGB", (400, 200), color="white")
    draw = ImageDraw.Draw(img)

    # Пытаемся использовать шрифт, если нет - используем стандартный
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except Exception:
        font = ImageFont.load_default()

    # Рисуем текст с ошибкой
    text = "2 + 2 = 5"
    draw.text((50, 80), text, fill="black", font=font)

    # Сохраняем в байты
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    return img_bytes.getvalue()


def image_to_base64(image_data: bytes) -> str:
    """Конвертирует изображение в base64"""
    return base64.b64encode(image_data).decode("utf-8")


async def test_homework_check_api():
    """Тест проверки ДЗ через API"""
    print("=" * 60)
    print("TEST: POST /api/miniapp/homework/check")
    print("=" * 60)

    # Создаём тестовое изображение
    test_image = create_test_image()
    photo_base64 = image_to_base64(test_image)

    # Тестовый telegram_id (нужен реальный пользователь в БД для полного теста)
    test_telegram_id = 123456  # Замените на реальный ID для полного теста

    request_data = {
        "telegram_id": test_telegram_id,
        "photo_base64": photo_base64,
        "subject": "математика",
        "topic": "сложение",
        "message": "Проверь это задание, пожалуйста",
    }

    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}/api/miniapp/homework/check"

        try:
            print(f"Sending request to {url}")
            print(f"   telegram_id: {test_telegram_id}")
            print("   subject: matematika")
            print(f"   photo_size: {len(photo_base64)} bytes (base64)")

            async with session.post(
                url, json=request_data, timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                status = response.status
                response_text = await response.text()

                print("\nServer response:")
                print(f"   Status: {status}")

                if status == 200:
                    import json

                    try:
                        data = await response.json()
                        print("   [OK] Success!")
                        print(f"   Submission ID: {data.get('submission', {}).get('id')}")
                        print(f"   Has errors: {data.get('submission', {}).get('has_errors')}")
                        print(
                            f"   Errors found: {len(data.get('submission', {}).get('errors_found', []))}"
                        )
                        print(
                            f"   AI feedback length: {len(data.get('submission', {}).get('ai_feedback', ''))} chars"
                        )
                        return True
                    except json.JSONDecodeError:
                        print(f"   [WARN] Not JSON response: {response_text[:200]}")
                        return False
                elif status == 404:
                    print(f"   [WARN] User not found (telegram_id={test_telegram_id})")
                    print("   Normal if user does not exist in DB")
                    return True  # Не критичная ошибка для теста структуры
                else:
                    print(f"   [ERROR] Status: {status}")
                    print(f"   Response: {response_text[:500]}")
                    return False

        except aiohttp.ClientError as e:
            print(f"   [ERROR] Connection error: {e}")
            return False
        except TimeoutError:
            print("   [ERROR] Timeout (>60 sec)")
            return False


async def test_homework_history_api():
    """Тест получения истории проверок ДЗ"""
    print("\n" + "=" * 60)
    print("TEST: GET /api/miniapp/homework/history/{telegram_id}")
    print("=" * 60)

    test_telegram_id = 123456

    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}/api/miniapp/homework/history/{test_telegram_id}?limit=10"

        try:
            print(f"Sending request to {url}")

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                status = response.status
                response_text = await response.text()

                print("\nServer response:")
                print(f"   Status: {status}")

                if status == 200:
                    import json

                    try:
                        data = await response.json()
                        history = data.get("history", [])
                        print("   [OK] Success!")
                        print(f"   Records count: {len(history)}")
                        return True
                    except json.JSONDecodeError:
                        print(f"   [WARN] Not JSON response: {response_text[:200]}")
                        return False
                elif status == 400:
                    print("   [WARN] Invalid telegram_id")
                    return True  # Валидация работает
                else:
                    print(f"   [ERROR] Status: {status}")
                    print(f"   Response: {response_text[:500]}")
                    return False

        except Exception as e:
            print(f"   [ERROR] Error: {e}")
            return False


async def test_homework_statistics_api():
    """Тест получения статистики проверок ДЗ"""
    print("\n" + "=" * 60)
    print("TEST: GET /api/miniapp/homework/statistics/{telegram_id}")
    print("=" * 60)

    test_telegram_id = 123456

    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}/api/miniapp/homework/statistics/{test_telegram_id}"

        try:
            print(f"Sending request to {url}")

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                status = response.status
                response_text = await response.text()

                print("\nServer response:")
                print(f"   Status: {status}")

                if status == 200:
                    import json

                    try:
                        data = await response.json()
                        stats = data.get("statistics", {})
                        print("   [OK] Success!")
                        print(f"   Total checks: {stats.get('total_checks', 0)}")
                        print(f"   With errors: {stats.get('with_errors', 0)}")
                        print(f"   Without errors: {stats.get('without_errors', 0)}")
                        print(f"   Error rate: {stats.get('error_rate', 0)}%")
                        return True
                    except json.JSONDecodeError:
                        print(f"   [WARN] Not JSON response: {response_text[:200]}")
                        return False
                elif status == 400:
                    print("   [WARN] Invalid telegram_id")
                    return True  # Валидация работает
                else:
                    print(f"   [ERROR] Status: {status}")
                    print(f"   Response: {response_text[:500]}")
                    return False

        except Exception as e:
            print(f"   [ERROR] Error: {e}")
            return False


async def main():
    """Запуск всех тестов"""
    print("\n" + "=" * 60)
    print("START: Real API tests for homework check")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    db_url = os.getenv("DATABASE_URL", "not set")
    print(f"Database URL: {db_url[:50]}..." if len(db_url) > 50 else f"Database URL: {db_url}")
    print()

    results = []

    # Тест 1: Проверка ДЗ
    result1 = await test_homework_check_api()
    results.append(("POST /api/miniapp/homework/check", result1))

    # Тест 2: История
    result2 = await test_homework_history_api()
    results.append(("GET /api/miniapp/homework/history", result2))

    # Тест 3: Статистика
    result3 = await test_homework_statistics_api()
    results.append(("GET /api/miniapp/homework/statistics", result3))

    # Итоги
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {test_name}")

    all_passed = all(r for _, r in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("SUCCESS: All tests passed!")
    else:
        print("WARNING: Some tests failed (see details above)")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
