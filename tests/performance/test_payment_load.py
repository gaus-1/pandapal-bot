"""
НАГРУЗОЧНЫЕ тесты для платежной системы
Использует Locust для симуляции реальной нагрузки

Тестируем:
- Создание платежей под нагрузкой
- Обработку webhook под нагрузкой
- Авторизацию через Telegram под нагрузкой
- Одновременные запросы от множества пользователей
- Производительность при пиковых нагрузках
"""

import hashlib
import hmac
import json
import random
import time
from typing import Dict

from locust import HttpUser, between, task

from bot.config import settings


class TelegramAuthLoadTest(HttpUser):
    """
    Нагрузочный тест для Telegram Login Widget
    Симулирует множество одновременных авторизаций
    """

    host = "http://localhost:8080"
    wait_time = between(1, 3)  # Пауза между запросами 1-3 сек

    def on_start(self):
        """Вызывается один раз при старте каждого виртуального пользователя"""
        # Генерируем уникальный telegram_id для этого пользователя
        self.telegram_id = random.randint(100000000, 999999999)
        self.telegram_data = self.create_valid_telegram_data(self.telegram_id)

    def create_valid_telegram_data(self, telegram_id: int) -> Dict:
        """Создаёт валидные данные от Telegram Login Widget"""
        auth_date = int(time.time())
        data = {
            "id": str(telegram_id),
            "first_name": f"LoadTest{telegram_id}",
            "last_name": "User",
            "username": f"loadtest_{telegram_id}",
            "auth_date": str(auth_date),
        }

        # Вычисляем hash как Telegram
        data_check_string = "\n".join([f"{key}={data[key]}" for key in sorted(data.keys())])
        secret_key = hashlib.sha256(settings.telegram_bot_token.encode()).digest()
        hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        data["hash"] = hash_value
        return data

    @task(3)
    def telegram_login(self):
        """
        Авторизация через Telegram Login Widget
        Вес 3 - выполняется чаще всех
        """
        with self.client.post(
            "/api/auth/telegram/login",
            json=self.telegram_data,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    response.success()
                else:
                    response.failure(f"Login failed: {data}")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(2)
    def create_payment(self):
        """
        Создание платежа через YooKassa
        Вес 2 - выполняется часто
        """
        payment_data = {
            "telegram_id": self.telegram_id,
            "plan_id": random.choice(["week", "month", "year"]),
            "amount": random.choice([99.0, 249.0, 1999.0]),
        }

        with self.client.post(
            "/api/miniapp/premium/create-payment",
            json=payment_data,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "confirmation_url" in data:
                    response.success()
                else:
                    response.failure(f"No confirmation URL in response: {data}")
            elif response.status_code == 404:
                # Пользователь не найден - это ожидаемо для load теста
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def check_user_profile(self):
        """
        Проверка профиля пользователя
        Вес 1 - выполняется реже
        """
        with self.client.get(
            f"/api/miniapp/user/{self.telegram_id}",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Пользователь не найден - создаём через auth
                self.telegram_login()
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class YooKassaWebhookLoadTest(HttpUser):
    """
    Нагрузочный тест для YooKassa webhook обработки
    Симулирует множество одновременных webhook от YooKassa
    """

    host = "http://localhost:8080"
    wait_time = between(0.5, 2)  # Webhook приходят чаще

    def on_start(self):
        """Инициализация"""
        self.payment_counter = 0

    @task
    def send_webhook(self):
        """
        Отправка webhook от YooKassa
        """
        self.payment_counter += 1
        telegram_id = random.randint(100000000, 999999999)
        plan_id = random.choice(["week", "month", "year"])

        webhook_data = {
            "type": "notification",
            "event": "payment.succeeded",
            "object": {
                "id": f"payment_load_{self.payment_counter}_{telegram_id}",
                "status": "succeeded",
                "amount": {
                    "value": str(random.choice([99.0, 249.0, 1999.0])),
                    "currency": "RUB",
                },
                "metadata": {
                    "telegram_id": str(telegram_id),
                    "plan_id": plan_id,
                },
                "paid": True,
                "payment_method": {"type": random.choice(["bank_card", "sbp", "yoo_money"])},
            },
        }

        # Вычисляем подпись webhook
        webhook_json = json.dumps(webhook_data)
        signature = hmac.new(
            settings.yookassa_secret_key.encode("utf-8"),
            webhook_json.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        with self.client.post(
            "/api/miniapp/premium/yookassa-webhook",
            data=webhook_json,
            headers={
                "Content-Type": "application/json",
                "X-Yookassa-Signature": signature,
            },
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Webhook failed: {response.status_code}")


class MixedPaymentLoadTest(HttpUser):
    """
    Смешанный нагрузочный тест
    Симулирует реальное поведение пользователей:
    1. Авторизация
    2. Просмотр планов
    3. Создание платежа
    4. Проверка статуса
    """

    host = "http://localhost:8080"
    wait_time = between(2, 5)

    def on_start(self):
        """Авторизация пользователя при старте"""
        self.telegram_id = random.randint(100000000, 999999999)
        self.is_authenticated = False
        self.authenticate()

    def authenticate(self):
        """Авторизация через Telegram"""
        auth_date = int(time.time())
        telegram_data = {
            "id": str(self.telegram_id),
            "first_name": f"User{self.telegram_id}",
            "auth_date": str(auth_date),
        }

        data_check_string = "\n".join(
            [f"{key}={telegram_data[key]}" for key in sorted(telegram_data.keys())]
        )
        secret_key = hashlib.sha256(settings.telegram_bot_token.encode()).digest()
        telegram_data["hash"] = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        response = self.client.post("/api/auth/telegram/login", json=telegram_data)
        if response.status_code == 200:
            self.is_authenticated = True

    @task(5)
    def view_premium_page(self):
        """Просмотр страницы Premium"""
        if not self.is_authenticated:
            self.authenticate()

        self.client.get("/")

    @task(3)
    def create_payment_flow(self):
        """
        Полный цикл создания платежа:
        1. Выбор плана
        2. Создание платежа
        3. Редирект на YooKassa
        """
        if not self.is_authenticated:
            self.authenticate()

        plan_id = random.choice(["week", "month", "year"])
        amounts = {"week": 99.0, "month": 249.0, "year": 1999.0}

        # Создаём платеж
        payment_data = {
            "telegram_id": self.telegram_id,
            "plan_id": plan_id,
            "amount": amounts[plan_id],
        }

        self.client.post("/api/miniapp/premium/create-payment", json=payment_data)

    @task(1)
    def check_premium_status(self):
        """Проверка статуса Premium"""
        if not self.is_authenticated:
            self.authenticate()

        self.client.get(f"/api/miniapp/user/{self.telegram_id}")


class StressTestPayments(HttpUser):
    """
    СТРЕСС-ТЕСТ: Экстремальная нагрузка на платёжную систему
    - Минимальные паузы между запросами
    - Максимальное количество одновременных пользователей
    - Тестирование отказоустойчивости
    """

    host = "http://localhost:8080"
    wait_time = between(0.1, 0.5)  # Очень частые запросы

    def on_start(self):
        self.telegram_id = random.randint(100000000, 999999999)
        self.request_counter = 0

    @task(10)
    def rapid_payment_creation(self):
        """Быстрое создание множества платежей"""
        self.request_counter += 1

        payment_data = {
            "telegram_id": self.telegram_id,
            "plan_id": "week",
            "amount": 99.0,
        }

        with self.client.post(
            "/api/miniapp/premium/create-payment",
            json=payment_data,
            catch_response=True,
            timeout=5,  # Таймаут 5 секунд
        ) as response:
            if response.elapsed.total_seconds() > 2:
                response.failure(f"Request took {response.elapsed.total_seconds()}s (too slow)")
            elif response.status_code in [200, 404]:
                response.success()
            elif response.status_code == 429:
                # Rate limit - это ожидаемо при стресс-тесте
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(5)
    def rapid_auth_requests(self):
        """Быстрые повторные авторизации"""
        auth_date = int(time.time())
        telegram_data = {
            "id": str(self.telegram_id),
            "first_name": "StressTest",
            "auth_date": str(auth_date),
        }

        data_check_string = "\n".join(
            [f"{key}={telegram_data[key]}" for key in sorted(telegram_data.keys())]
        )
        secret_key = hashlib.sha256(settings.telegram_bot_token.encode()).digest()
        telegram_data["hash"] = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        with self.client.post(
            "/api/auth/telegram/login",
            json=telegram_data,
            catch_response=True,
            timeout=5,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()  # Rate limit ожидаем
            else:
                response.failure(f"Auth failed: {response.status_code}")


# Сценарии нагрузочного тестирования:
#
# 1. Нормальная нагрузка:
#    locust -f tests/performance/test_payment_load.py --users 100 --spawn-rate 10
#
# 2. Высокая нагрузка:
#    locust -f tests/performance/test_payment_load.py --users 500 --spawn-rate 50
#
# 3. Стресс-тест:
#    locust -f tests/performance/test_payment_load.py --users 1000 --spawn-rate 100 -c StressTestPayments
#
# 4. Webhook нагрузка:
#    locust -f tests/performance/test_payment_load.py --users 200 --spawn-rate 20 -c YooKassaWebhookLoadTest
#
# 5. Смешанный тест:
#    locust -f tests/performance/test_payment_load.py --users 300 --spawn-rate 30 -c MixedPaymentLoadTest
