"""
Интеграционные тесты «ленивой панды» в Mini App API.

Проверяют реальный endpoint POST /api/miniapp/ai/chat:
- после 15 сообщений пользователя за 20 минут возвращается ответ «ленивой» панды;
- до 15 сообщений запрос идёт в AI и возвращается обычный ответ (с моком AI).
"""

import json
import os
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.test_utils import make_mocked_request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, ChatHistory, User


@pytest.mark.integration
class TestPandaLazyMiniappReal:
    """Реальные тесты ленивой панды в Mini App chat API."""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Реальная SQLite БД для каждого теста."""
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

    @pytest.fixture
    def test_user(self, real_db_session):
        """Тестовый пользователь."""
        user = User(
            telegram_id=900001,
            username="lazy_test_user",
            first_name="Lazy",
            last_name="Test",
            user_type="child",
            age=10,
            grade=5,
        )
        real_db_session.add(user)
        real_db_session.commit()
        return user

    def _create_chat_request(self, telegram_id: int, message: str = "Привет"):
        """Мок POST /api/miniapp/ai/chat с JSON body."""
        request = make_mocked_request(
            "POST",
            "/api/miniapp/ai/chat",
            headers={"Content-Type": "application/json"},
        )
        payload = {"telegram_id": telegram_id, "message": message}
        request._json_data = payload

        async def json():
            return request._json_data

        request.json = json
        type(request).remote = property(lambda self: "127.0.0.1")
        return request

    @contextmanager
    def _patch_db_and_auth(self, real_db_session):
        """Патч get_db и require_owner для вызова реального handler с тестовой БД."""

        def fake_get_db():
            class Ctx:
                def __enter__(self):
                    return real_db_session

                def __exit__(self, *args):
                    real_db_session.commit()
                    return None

            return Ctx()

        with (
            patch("bot.api.miniapp.chat.get_db", fake_get_db),
            patch("bot.api.miniapp.chat.require_owner", return_value=None),
        ):
            yield

    @pytest.mark.asyncio
    async def test_lazy_response_after_15_messages_in_miniapp(self, real_db_session, test_user):
        """
        После 15 сообщений пользователя за 20 минут Mini App chat
        возвращает ответ «ленивой» панды (без вызова YandexGPT).
        """
        from bot.api.miniapp import miniapp_ai_chat

        telegram_id = test_user.telegram_id
        now = datetime.now(UTC)
        # Все сообщения в пределах последних 20 минут
        for i in range(15):
            msg = ChatHistory(
                user_telegram_id=telegram_id,
                message_text=f"Сообщение {i + 1}",
                message_type="user",
                timestamp=now - timedelta(minutes=19) + timedelta(seconds=i),
            )
            real_db_session.add(msg)
        real_db_session.commit()

        request = self._create_chat_request(telegram_id, "Ещё один вопрос")

        with self._patch_db_and_auth(real_db_session):
            response = await miniapp_ai_chat(request)

        assert response.status == 200
        data = json.loads(response.body.decode()) if response.body else {}
        assert "response" in data
        text = data["response"]
        # Ожидаемые фразы ленивой панды
        assert "бамбук" in text or "лениво" in text or "попозже" in text

    @pytest.mark.asyncio
    async def test_no_lazy_before_15_messages_in_miniapp(self, real_db_session, test_user):
        """
        До 15 сообщений за 20 минут запрос идёт в AI; при замоканном
        generate_response возвращается обычный ответ.
        """
        from bot.api.miniapp import miniapp_ai_chat

        telegram_id = test_user.telegram_id
        now = datetime.now(UTC)
        for i in range(5):
            msg = ChatHistory(
                user_telegram_id=telegram_id,
                message_text=f"Вопрос {i + 1}",
                message_type="user",
                timestamp=now - timedelta(minutes=5) + timedelta(seconds=i),
            )
            real_db_session.add(msg)
        real_db_session.commit()

        request = self._create_chat_request(telegram_id, "Что такое фотосинтез?")

        fake_response = "Тестовый ответ панды про фотосинтез."

        with (
            self._patch_db_and_auth(real_db_session),
            patch("bot.api.miniapp.chat.get_ai_service") as mock_get_ai,
        ):
            mock_service = mock_get_ai.return_value
            mock_service.generate_response = AsyncMock(return_value=fake_response)

            response = await miniapp_ai_chat(request)

        assert response.status == 200
        data = json.loads(response.body.decode()) if response.body else {}
        assert "response" in data
        assert data["response"] == fake_response

    @pytest.mark.asyncio
    async def test_rest_offer_after_10_exchanges_in_miniapp(self, real_db_session, test_user):
        """
        После 10 ответов подряд (consecutive_since_rest=10) следующий запрос
        возвращает предложение отдыха/игры без вызова YandexGPT.
        """
        from bot.api.miniapp import miniapp_ai_chat

        telegram_id = test_user.telegram_id
        test_user.consecutive_since_rest = 10
        test_user.rest_offers_count = 0
        test_user.last_ai_was_rest = False
        real_db_session.commit()

        request = self._create_chat_request(telegram_id, "Ещё один вопрос")

        with self._patch_db_and_auth(real_db_session):
            response = await miniapp_ai_chat(request)

        assert response.status == 200
        data = json.loads(response.body.decode()) if response.body else {}
        assert "response" in data
        text = data["response"]
        assert "поиграем" in text or "перерыв" in text or "отдохнуть" in text

    @pytest.mark.asyncio
    async def test_continue_after_rest_offer_in_miniapp(self, real_db_session, test_user):
        """
        Если пользователь после предложения отдыха пишет «продолжай»,
        панда соглашается и возвращает «Хорошо, давай продолжать!» без вызова AI.
        """
        from bot.api.miniapp import miniapp_ai_chat

        telegram_id = test_user.telegram_id
        test_user.last_ai_was_rest = True
        test_user.rest_offers_count = 1
        real_db_session.commit()

        request = self._create_chat_request(telegram_id, "Продолжай, хочу учиться")

        with self._patch_db_and_auth(real_db_session):
            response = await miniapp_ai_chat(request)

        assert response.status == 200
        data = json.loads(response.body.decode()) if response.body else {}
        assert "response" in data
        assert "продолжать" in data["response"]

    @pytest.mark.asyncio
    async def test_refuse_after_rest_offer_returns_continue_not_games(
        self, real_db_session, test_user
    ):
        """
        После предложения отдыха ответ «Нет» даёт «давай продолжать», не «Заходи в Игры».
        """
        from bot.api.miniapp import miniapp_ai_chat

        telegram_id = test_user.telegram_id
        test_user.last_ai_was_rest = True
        test_user.rest_offers_count = 1
        real_db_session.commit()

        request = self._create_chat_request(telegram_id, "Нет")

        with self._patch_db_and_auth(real_db_session):
            response = await miniapp_ai_chat(request)

        assert response.status == 200
        data = json.loads(response.body.decode()) if response.body else {}
        assert "response" in data
        text = data["response"]
        assert "продолжать" in text
        assert "Игры" not in text
