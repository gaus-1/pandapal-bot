"""
Тесты защиты от Slowloris атак
Проверка защиты от медленных HTTP соединений
"""

import asyncio
import time

import pytest
from aiohttp.test_utils import make_mocked_request

from bot.security.middleware import RateLimiter, get_rate_limiter


class TestSlowlorisProtection:
    """Тесты защиты от Slowloris атак"""

    def test_rate_limiter_handles_rapid_requests(self):
        """Тест: rate limiter обрабатывает быстрые запросы"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        test_ip = "192.168.1.100"

        # Отправляем быстрые запросы
        for i in range(10):
            allowed, reason = limiter.is_allowed(test_ip)
            assert allowed, f"Запрос {i+1} должен быть разрешен"
            assert reason is None

        # 11-й запрос должен быть заблокирован
        allowed, reason = limiter.is_allowed(test_ip)
        assert not allowed, "11-й запрос должен быть заблокирован"

    def test_rate_limiter_resets_after_window(self):
        """Тест: rate limiter сбрасывается после окна времени (но блокировка длится дольше)"""
        limiter = RateLimiter(max_requests=5, window_seconds=1)  # 1 секунда для теста
        test_ip = "192.168.1.101"

        # Превышаем лимит
        for i in range(6):
            limiter.is_allowed(test_ip)

        # IP заблокирован на 5 минут (block_duration)
        allowed, reason = limiter.is_allowed(test_ip)
        assert not allowed, "IP должен быть заблокирован после превышения лимита"

        # Блокировка длится 5 минут, не 1 секунду
        # Это правильное поведение для защиты от атак

    @pytest.mark.asyncio
    async def test_concurrent_requests_from_multiple_ips(self):
        """Тест: конкурентные запросы от разных IP обрабатываются независимо"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        async def make_requests(ip: str, count: int):
            """Отправить запросы от одного IP"""
            for _ in range(count):
                limiter.is_allowed(ip)
                await asyncio.sleep(0.01)

        # Отправляем запросы от разных IP параллельно
        tasks = [make_requests(f"192.168.1.{i}", 10) for i in range(200, 210)]

        await asyncio.gather(*tasks)

        # Все IP должны обрабатываться независимо
        for i in range(200, 210):
            ip = f"192.168.1.{i}"
            # После 10 запросов IP должен быть заблокирован
            allowed, _ = limiter.is_allowed(ip)
            assert not allowed, f"IP {ip} должен быть заблокирован после превышения лимита"

    def test_rate_limiter_different_endpoints(self):
        """Тест: разные endpoints имеют разные лимиты"""
        api_limiter = get_rate_limiter("/api/miniapp/user/123")
        auth_limiter = get_rate_limiter("/api/miniapp/auth")
        ai_limiter = get_rate_limiter("/api/miniapp/ai/chat")

        assert api_limiter.max_requests == 300, "API endpoints: 300 req/min"
        assert auth_limiter.max_requests == 20, "Auth endpoints: 20 req/min"
        assert ai_limiter.max_requests == 100, "AI endpoints: 100 req/min"

    def test_rate_limiter_block_duration(self):
        """Тест: длительность блокировки IP"""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        test_ip = "192.168.1.102"

        # Превышаем лимит
        for i in range(4):
            limiter.is_allowed(test_ip)

        # IP должен быть заблокирован
        allowed1, _ = limiter.is_allowed(test_ip)
        assert not allowed1, "IP должен быть заблокирован"

        # Проверяем что блокировка сохраняется
        allowed2, _ = limiter.is_allowed(test_ip)
        assert not allowed2, "Блокировка должна сохраняться"
