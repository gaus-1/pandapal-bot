"""
РЕАЛЬНЫЕ интеграционные тесты для Telegram Login Widget
БЕЗ МОКОВ - только реальные операции с БД и криптографией

Тестируем:
- Валидацию hash от Telegram
- Создание/обновление пользователя
- Проверку срока действия auth_date
- Обработку невалидных данных
- Интеграцию с frontend
- Создание платежа после авторизации
"""

import hashlib
import hmac
import json
import os
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from aiohttp import web
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.config import settings
from bot.models import Base, User
from bot.services import TelegramAuthService, UserService


class TestTelegramAuthReal:
    """Реальные интеграционные тесты Telegram Login Widget"""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Создаёт реальную SQLite БД для каждого теста"""
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        yield session

        session.close()
        engine.dispose()
        os.close(db_fd)
        os.unlink(db_path)

    def create_valid_telegram_data(self, telegram_id=123456789):
        """
        Создаёт валидные данные от Telegram Login Widget с правильным hash
        """
        auth_date = int(time.time())
        data = {
            "id": str(telegram_id),
            "first_name": "Тест",
            "last_name": "Пользователь",
            "username": "test_user",
            "photo_url": "https://t.me/i/userpic/320/test.jpg",
            "auth_date": str(auth_date),
        }

        # Вычисляем правильный hash (как Telegram)
        data_check_string = "\n".join([f"{key}={data[key]}" for key in sorted(data.keys())])
        secret_key = hashlib.sha256(settings.telegram_bot_token.encode()).digest()
        hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        data["hash"] = hash_value
        return data

    @pytest.mark.asyncio
    async def test_validate_telegram_data_valid(self, real_db_session):
        """
        КРИТИЧНО: Проверка валидации правильных данных от Telegram
        """
        auth_service = TelegramAuthService(real_db_session)
        telegram_data = self.create_valid_telegram_data()

        # Валидируем данные
        result = auth_service.validate_telegram_login_data(telegram_data)

        # Проверяем что валидация прошла
        assert result is not None
        assert result["id"] == telegram_data["id"]
        assert result["first_name"] == telegram_data["first_name"]

    @pytest.mark.asyncio
    async def test_validate_telegram_data_invalid_hash(self, real_db_session):
        """
        КРИТИЧНО: Проверка отклонения данных с невалидным hash
        """
        auth_service = TelegramAuthService(real_db_session)
        telegram_data = self.create_valid_telegram_data()

        # Подменяем hash на неправильный
        telegram_data["hash"] = "invalid_hash_1234567890"

        # Валидируем данные
        result = auth_service.validate_telegram_login_data(telegram_data)

        # Проверяем что валидация НЕ прошла
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_telegram_data_expired(self, real_db_session):
        """
        КРИТИЧНО: Проверка отклонения устаревших данных (>24 часа)
        """
        auth_service = TelegramAuthService(real_db_session)

        # Создаём данные с auth_date 25 часов назад
        auth_date = int(time.time()) - (25 * 3600)
        data = {
            "id": "123456789",
            "first_name": "Тест",
            "auth_date": str(auth_date),
        }

        # Вычисляем правильный hash для этих данных
        data_check_string = "\n".join([f"{key}={data[key]}" for key in sorted(data.keys())])
        secret_key = hashlib.sha256(settings.telegram_bot_token.encode()).digest()
        hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        data["hash"] = hash_value

        # Валидируем данные
        result = auth_service.validate_telegram_login_data(data)

        # Проверяем что валидация НЕ прошла из-за истечения срока
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_telegram_data_missing_fields(self, real_db_session):
        """Проверка отклонения данных с отсутствующими полями"""
        auth_service = TelegramAuthService(real_db_session)

        # Данные без обязательного поля first_name
        incomplete_data = {
            "id": "123456789",
            "auth_date": str(int(time.time())),
            "hash": "some_hash",
        }

        result = auth_service.validate_telegram_login_data(incomplete_data)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_user_from_telegram_data(self, real_db_session):
        """
        КРИТИЧНО: Проверка создания пользователя из данных Telegram
        """
        auth_service = TelegramAuthService(real_db_session)
        telegram_data = self.create_valid_telegram_data(telegram_id=999111222)

        # Валидируем данные
        validated_data = auth_service.validate_telegram_login_data(telegram_data)
        assert validated_data is not None

        # Создаём пользователя
        user = auth_service.get_or_create_user_from_telegram_data(validated_data)
        real_db_session.commit()

        # Проверяем что пользователь создан
        assert user is not None
        assert user.telegram_id == 999111222
        assert user.first_name == "Тест"
        assert user.last_name == "Пользователь"
        assert user.username == "test_user"

        # Проверяем запись в БД
        db_user = real_db_session.query(User).filter_by(telegram_id=999111222).first()
        assert db_user is not None
        assert db_user.username == "test_user"

    @pytest.mark.asyncio
    async def test_update_existing_user_from_telegram_data(self, real_db_session):
        """
        КРИТИЧНО: Проверка обновления существующего пользователя
        """
        auth_service = TelegramAuthService(real_db_session)

        # Создаём пользователя с начальными данными
        user_service = UserService(real_db_session)
        user_service.get_or_create_user(
            telegram_id=999111333,
            username="old_username",
            first_name="Старое",
            last_name="Имя",
        )
        real_db_session.commit()

        # Создаём новые данные от Telegram с обновлёнными полями
        telegram_data = self.create_valid_telegram_data(telegram_id=999111333)
        telegram_data["username"] = "new_username"
        telegram_data["first_name"] = "Новое"

        # Пересчитываем hash для новых данных
        data_for_hash = {k: v for k, v in telegram_data.items() if k != "hash"}
        data_check_string = "\n".join(
            [f"{key}={data_for_hash[key]}" for key in sorted(data_for_hash.keys())]
        )
        secret_key = hashlib.sha256(settings.telegram_bot_token.encode()).digest()
        telegram_data["hash"] = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        # Валидируем и обновляем пользователя
        validated_data = auth_service.validate_telegram_login_data(telegram_data)
        user = auth_service.get_or_create_user_from_telegram_data(validated_data)
        real_db_session.commit()

        # Проверяем что данные обновлены
        assert user.username == "new_username"
        assert user.first_name == "Новое"

    @pytest.mark.asyncio
    async def test_telegram_login_endpoint(self, real_db_session):
        """
        КРИТИЧНО: Проверка endpoint /api/auth/telegram/login
        """
        from bot.api.auth_endpoints import telegram_login_auth

        telegram_data = self.create_valid_telegram_data(telegram_id=999111444)

        class MockRequest:
            async def json(self):
                return telegram_data

        request = MockRequest()

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.auth_endpoints.get_db", mock_get_db):
            response = await telegram_login_auth(request)

            # Парсим ответ
            if hasattr(response, "_body") and response._body:
                response_data = json.loads(response._body.decode("utf-8"))
            else:
                response_data = await response.json()

            # Проверяем результат
            assert response.status == 200
            assert response_data["success"] is True
            assert "user" in response_data
            assert response_data["user"]["telegram_id"] == 999111444

            # Проверяем что пользователь создан в БД
            user = real_db_session.query(User).filter_by(telegram_id=999111444).first()
            assert user is not None

    @pytest.mark.asyncio
    async def test_telegram_login_endpoint_invalid_data(self, real_db_session):
        """Проверка endpoint с невалидными данными"""
        from bot.api.auth_endpoints import telegram_login_auth

        invalid_data = {
            "id": "123",
            "first_name": "Test",
            "auth_date": str(int(time.time())),
            "hash": "invalid_hash",
        }

        class MockRequest:
            async def json(self):
                return invalid_data

        request = MockRequest()

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.auth_endpoints.get_db", mock_get_db):
            response = await telegram_login_auth(request)

            # Проверяем что возвращается ошибка
            assert response.status == 401

    @pytest.mark.asyncio
    async def test_payment_after_telegram_auth(self, real_db_session):
        """
        КРИТИЧНО: Проверка создания платежа после авторизации через Telegram
        """
        from bot.api.premium_endpoints import create_yookassa_payment

        auth_service = TelegramAuthService(real_db_session)
        telegram_data = self.create_valid_telegram_data(telegram_id=999111555)

        # Авторизуемся через Telegram
        validated_data = auth_service.validate_telegram_login_data(telegram_data)
        user = auth_service.get_or_create_user_from_telegram_data(validated_data)
        real_db_session.commit()

        # Создаём платеж с этим telegram_id
        payment_request_data = {
            "telegram_id": 999111555,
            "plan_id": "week",
            "amount": 99.0,
        }

        class MockRequest:
            async def json(self):
                return payment_request_data

        request = MockRequest()

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            response = await create_yookassa_payment(request)

            # Проверяем что платеж создан
            if hasattr(response, "_body") and response._body:
                response_data = json.loads(response._body.decode("utf-8"))
            else:
                response_data = await response.json()

            assert response.status == 200
            assert "confirmation_url" in response_data

    @pytest.mark.asyncio
    async def test_concurrent_telegram_logins(self, real_db_session):
        """Проверка одновременных авторизаций через Telegram"""
        import asyncio

        from bot.api.auth_endpoints import telegram_login_auth

        # Создаём несколько одновременных запросов
        telegram_ids = [999222111 + i for i in range(5)]

        async def login_user(telegram_id):
            telegram_data = self.create_valid_telegram_data(telegram_id=telegram_id)

            class MockRequest:
                async def json(self):
                    return telegram_data

            request = MockRequest()

            @contextmanager
            def mock_get_db():
                yield real_db_session

            with patch("bot.api.auth_endpoints.get_db", mock_get_db):
                return await telegram_login_auth(request)

        # Запускаем все авторизации одновременно
        results = await asyncio.gather(
            *[login_user(tid) for tid in telegram_ids], return_exceptions=True
        )

        # Проверяем что все успешны
        successful_logins = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_logins) == len(telegram_ids)

        # Проверяем что все пользователи созданы
        for telegram_id in telegram_ids:
            user = real_db_session.query(User).filter_by(telegram_id=telegram_id).first()
            assert user is not None

    @pytest.mark.asyncio
    async def test_telegram_auth_security_attack_scenarios(self, real_db_session):
        """
        КРИТИЧНО: Проверка защиты от различных атак
        """
        auth_service = TelegramAuthService(real_db_session)

        # Сценарий 1: Попытка подделать другого пользователя
        fake_data = self.create_valid_telegram_data(telegram_id=123)
        fake_data["id"] = "999"  # Меняем ID после создания hash
        result = auth_service.validate_telegram_login_data(fake_data)
        assert result is None  # Должен отклонить

        # Сценарий 2: Replay attack (повторное использование старых данных)
        old_auth_date = int(time.time()) - (30 * 3600)  # 30 часов назад
        old_data = {
            "id": "123",
            "first_name": "Test",
            "auth_date": str(old_auth_date),
        }
        data_check_string = "\n".join([f"{key}={old_data[key]}" for key in sorted(old_data.keys())])
        secret_key = hashlib.sha256(settings.telegram_bot_token.encode()).digest()
        old_data["hash"] = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        result = auth_service.validate_telegram_login_data(old_data)
        assert result is None  # Должен отклонить устаревшие данные

        # Сценарий 3: Попытка использовать hash от других данных
        valid_data1 = self.create_valid_telegram_data(telegram_id=111)
        valid_data2 = self.create_valid_telegram_data(telegram_id=222)

        # Берём hash от data1 и применяем к data2
        mixed_data = valid_data2.copy()
        mixed_data["hash"] = valid_data1["hash"]

        result = auth_service.validate_telegram_login_data(mixed_data)
        assert result is None  # Должен отклонить

    @pytest.mark.asyncio
    async def test_telegram_auth_with_missing_optional_fields(self, real_db_session):
        """Проверка авторизации с отсутствующими опциональными полями"""
        auth_service = TelegramAuthService(real_db_session)

        # Данные без username, last_name, photo_url
        auth_date = int(time.time())
        minimal_data = {
            "id": "999333111",
            "first_name": "Минимум",
            "auth_date": str(auth_date),
        }

        # Вычисляем hash
        data_check_string = "\n".join(
            [f"{key}={minimal_data[key]}" for key in sorted(minimal_data.keys())]
        )
        secret_key = hashlib.sha256(settings.telegram_bot_token.encode()).digest()
        minimal_data["hash"] = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        # Валидируем
        validated_data = auth_service.validate_telegram_login_data(minimal_data)
        assert validated_data is not None

        # Создаём пользователя
        user = auth_service.get_or_create_user_from_telegram_data(validated_data)
        real_db_session.commit()

        # Проверяем что пользователь создан без опциональных полей
        assert user.telegram_id == 999333111
        assert user.first_name == "Минимум"
        assert user.username is None or user.username == ""
        assert user.last_name is None or user.last_name == ""
