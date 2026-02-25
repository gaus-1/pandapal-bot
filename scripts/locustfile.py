"""
Точка входа для нагрузочного тестирования Locust.

Использование (из корня проекта):
  locust -f scripts/locustfile.py
  locust -f scripts/locustfile.py --host=http://localhost:8080 --users 100 --spawn-rate 10
  locust -f scripts/locustfile.py --headless -u 50 -r 5 -t 30s
  locust -f scripts/locustfile.py -c TelegramAuthLoadTest --users 50
"""

import os

from tests.performance.test_payment_load import (
    MixedPaymentLoadTest,
    StressTestPayments,
    TelegramAuthLoadTest,
    YooKassaWebhookLoadTest,
)

# Host переопределяется через --host или env LOCUST_HOST (Locust читает сам)
_DEFAULT_HOST = os.getenv("LOCUST_HOST", "http://localhost:8080")
for cls in (
    TelegramAuthLoadTest,
    YooKassaWebhookLoadTest,
    MixedPaymentLoadTest,
    StressTestPayments,
):
    if getattr(cls, "host", None) == "http://localhost:8080":
        cls.host = _DEFAULT_HOST
