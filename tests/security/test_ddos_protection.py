"""
РЕАЛЬНЫЕ тесты защиты от DDOS атак
Проверка rate limiting работает корректно
"""

import time

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from bot.security.middleware import RateLimiter, get_rate_limiter


class TestDDoSProtection:
    """Тесты защиты от DDOS"""

    def test_rate_limiter_allows_normal_requests(self):
        """Тест: rate limiter разрешает нормальные запросы"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        test_ip = "192.168.1.1"

        # Отправляем 5 запросов (в пределах лимита)
        for i in range(5):
            allowed, reason = limiter.is_allowed(test_ip)
            assert allowed, f"Запрос {i+1} должен быть разрешен"
            assert reason is None

    def test_rate_limiter_blocks_excessive_requests(self):
        """Тест: rate limiter блокирует избыточные запросы"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        test_ip = "192.168.1.2"

        # Отправляем 5 запросов (лимит)
        for i in range(5):
            allowed, reason = limiter.is_allowed(test_ip)
            assert allowed, f"Запрос {i+1} должен быть разрешен"

        # 6-й запрос должен быть заблокирован
        allowed, reason = limiter.is_allowed(test_ip)
        assert not allowed, "6-й запрос должен быть заблокирован"
        assert "Rate limit exceeded" in reason or "blocked" in reason.lower()

    def test_rate_limiter_blocks_ip_after_limit(self):
        """Тест: IP блокируется после превышения лимита"""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        test_ip = "192.168.1.3"

        # Превышаем лимит
        for i in range(4):
            limiter.is_allowed(test_ip)

        # Следующие запросы должны быть заблокированы
        allowed, reason = limiter.is_allowed(test_ip)
        assert not allowed, "IP должен быть заблокирован"
        assert "blocked" in reason.lower() or "exceeded" in reason.lower()

    def test_rate_limiter_different_ips_independent(self):
        """Тест: разные IP обрабатываются независимо"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        ip1 = "192.168.1.10"
        ip2 = "192.168.1.11"

        # IP1 превышает лимит
        for i in range(6):
            limiter.is_allowed(ip1)

        # IP2 должен работать нормально
        allowed, reason = limiter.is_allowed(ip2)
        assert allowed, "IP2 должен работать независимо от IP1"
        assert reason is None

    def test_rate_limiter_window_reset(self):
        """Тест: окно лимита сбрасывается через время"""
        limiter = RateLimiter(max_requests=3, window_seconds=1)  # 1 секунда для теста
        test_ip = "192.168.1.4"

        # Превышаем лимит
        for i in range(4):
            limiter.is_allowed(test_ip)

        # Ждем истечения окна
        time.sleep(1.1)

        # Запрос должен быть разрешен снова
        allowed, reason = limiter.is_allowed(test_ip)
        assert allowed, "После истечения окна запрос должен быть разрешен"

    def test_rate_limiter_api_endpoint(self):
        """Тест: rate limiter для API endpoints"""
        limiter = get_rate_limiter("/api/miniapp/user/123")
        assert limiter.max_requests == 60, "API endpoints: 60 req/min"

    def test_rate_limiter_auth_endpoint(self):
        """Тест: rate limiter для auth endpoints"""
        limiter = get_rate_limiter("/api/miniapp/auth")
        assert limiter.max_requests == 10, "Auth endpoints: 10 req/min"

    def test_rate_limiter_ai_endpoint(self):
        """Тест: rate limiter для AI endpoints"""
        limiter = get_rate_limiter("/api/miniapp/ai/chat")
        assert limiter.max_requests == 30, "AI endpoints: 30 req/min"

    def test_rate_limiter_block_duration(self):
        """Тест: длительность блокировки IP"""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        test_ip = "192.168.1.5"

        # Превышаем лимит
        for i in range(3):
            limiter.is_allowed(test_ip)

        # IP должен быть заблокирован
        allowed1, _ = limiter.is_allowed(test_ip)
        assert not allowed1, "IP должен быть заблокирован"

        # Проверяем что блокировка сохраняется
        allowed2, _ = limiter.is_allowed(test_ip)
        assert not allowed2, "Блокировка должна сохраняться"
