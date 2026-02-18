"""
Интеграционные тесты реакций панды в чате (chat-stream).

Проверяют, что при позитивном/негативном фидбеке в event: final
приходит pandaReaction из нужного набора.
Требуют SQLite (DATABASE_URL с sqlite) для изоляции; при PostgreSQL — пропуск.
"""

import json
import os
import re
import tempfile
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.api.miniapp import setup_miniapp_routes
from bot.database import get_db
from bot.models import Base, User


def _use_sqlite_db() -> bool:
    """Проверка что тесты используют SQLite (изоляция, без реального PostgreSQL)."""
    url = os.getenv("DATABASE_URL", "")
    return "sqlite" in url.lower()


def _parse_sse_final_event(body: bytes) -> dict | None:
    """Из тела SSE-ответа извлечь data из первого event: final."""
    text = body.decode("utf-8", errors="replace")
    # События разделены двойным переносом
    for block in text.split("\n\n"):
        if not block.strip():
            continue
        event_type = None
        data_str = None
        for line in block.split("\n"):
            if line.startswith("event: "):
                event_type = line[7:].strip()
            elif line.startswith("data: "):
                data_str = line[6:].strip()
        if event_type == "final" and data_str:
            try:
                return json.loads(data_str)
            except json.JSONDecodeError:
                pass
    return None


@pytest.mark.integration
@pytest.mark.skipif(
    not _use_sqlite_db(),
    reason="Требуется DATABASE_URL с sqlite для изоляции (без реального PostgreSQL)",
)
class TestPandaChatReactionsStream:
    """Интеграционные тесты pandaReaction в chat-stream."""

    @pytest.fixture(scope="class")
    def test_db_engine(self):
        """SQLite БД для тестов класса."""
        fd, path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{path}", echo=False)
        Base.metadata.create_all(engine)
        yield engine
        engine.dispose()
        try:
            os.close(fd)
            os.unlink(path)
        except (OSError, PermissionError):
            pass

    @pytest.fixture(scope="class")
    def test_telegram_id(self):
        return 888001

    @pytest.fixture(scope="class")
    def test_user(self, test_db_engine, test_telegram_id):
        """Тестовый пользователь в БД. Возвращаем telegram_id, чтобы не держать сессию."""
        Session = sessionmaker(bind=test_db_engine)
        session = Session()
        user = User(
            telegram_id=test_telegram_id,
            username="panda_react_test",
            first_name="Test",
            last_name="User",
            user_type="child",
            age=12,
            grade=6,
        )
        session.add(user)
        session.commit()
        session.close()
        return {"telegram_id": test_telegram_id}

    @contextmanager
    def _patch_db_and_services(self, test_db_engine, test_user):
        """Патч get_db и сервисов для прохождения потока без реального Yandex."""

        Session = sessionmaker(bind=test_db_engine)

        def fake_get_db():
            class Ctx:
                def __enter__(self):
                    return Session()

                def __exit__(self, *args):
                    return None

            return Ctx()

        async def fake_stream(*args, **kwargs):
            yield "Рад был помочь!"

        mock_yandex = AsyncMock()
        mock_yandex.generate_text_response_stream = fake_stream

        mock_knowledge = AsyncMock()
        mock_knowledge.enhanced_search = AsyncMock(return_value=[])
        mock_knowledge.format_knowledge_for_ai = lambda materials: ""

        class MockResponseGenerator:
            yandex_service = mock_yandex
            knowledge_service = mock_knowledge
            _should_use_wikipedia = lambda self, msg: False

        class MockAIService:
            response_generator = MockResponseGenerator()

        def mock_get_ai_service():
            return MockAIService()

        with (
            patch("bot.database.get_db", fake_get_db),
            patch("bot.database.engine.get_db", fake_get_db),
            patch("bot.api.miniapp.stream_handlers._pre_checks.get_db", fake_get_db),
            patch("bot.api.miniapp.stream_handlers.ai_chat_stream.get_db", fake_get_db),
            patch(
                "bot.api.miniapp.stream_handlers.ai_chat_stream.verify_resource_owner",
                return_value=(True, None),
            ),
            patch(
                "bot.services.panda_lazy_service.PandaLazyService.check_and_update_lazy_state",
                return_value=(False, None),
            ),
            patch(
                "bot.services.premium_features_service.PremiumFeaturesService.can_make_ai_request",
                return_value=(True, ""),
            ),
            patch(
                "bot.api.miniapp.stream_handlers.ai_chat_stream.get_ai_service",
                side_effect=mock_get_ai_service,
            ),
        ):
            yield

    @pytest.fixture
    def app(self):
        """Минимальное aiohttp-приложение с miniapp routes (в т.ч. chat-stream)."""
        app = web.Application(client_max_size=25 * 1024 * 1024)
        setup_miniapp_routes(app)
        return app

    @pytest.mark.asyncio
    async def test_stream_final_has_panda_reaction_positive(
        self, app, test_db_engine, test_user, test_telegram_id
    ):
        """При позитивном сообщении в event: final есть pandaReaction из (happy, eating)."""
        with self._patch_db_and_services(test_db_engine, test_user):
            async with TestClient(TestServer(app)) as client:
                resp = await client.post(
                    "/api/miniapp/ai/chat-stream",
                    json={
                        "telegram_id": test_telegram_id,
                        "message": "спасибо, хороший ответ, мне понравилось",
                    },
                    headers={"Content-Type": "application/json"},
                )
                assert resp.status == 200, await resp.text()
                body = await resp.read()
                data = _parse_sse_final_event(body)
                assert data is not None, "Нет event: final в ответе"
                assert "content" in data
                assert "pandaReaction" in data
                assert data["pandaReaction"] in ("happy", "eating")

    @pytest.mark.asyncio
    async def test_stream_final_has_panda_reaction_negative(
        self, app, test_db_engine, test_user, test_telegram_id
    ):
        """При негативном сообщении в event: final есть pandaReaction из (offended, questioning)."""
        with self._patch_db_and_services(test_db_engine, test_user):
            async with TestClient(TestServer(app)) as client:
                resp = await client.post(
                    "/api/miniapp/ai/chat-stream",
                    json={
                        "telegram_id": test_telegram_id,
                        "message": "плохо, не то",
                    },
                    headers={"Content-Type": "application/json"},
                )
                assert resp.status == 200, await resp.text()
                body = await resp.read()
                data = _parse_sse_final_event(body)
                assert data is not None
                assert "pandaReaction" in data
                assert data["pandaReaction"] in ("offended", "questioning")

    @pytest.mark.asyncio
    async def test_stream_final_no_panda_reaction_neutral(
        self, app, test_db_engine, test_user, test_telegram_id
    ):
        """При нейтральном учебном сообщении в event: final нет pandaReaction."""
        with self._patch_db_and_services(test_db_engine, test_user):
            async with TestClient(TestServer(app)) as client:
                resp = await client.post(
                    "/api/miniapp/ai/chat-stream",
                    json={
                        "telegram_id": test_telegram_id,
                        "message": "как решить уравнение 2x + 5 = 13?",
                    },
                    headers={"Content-Type": "application/json"},
                )
                assert resp.status == 200
                body = await resp.read()
                data = _parse_sse_final_event(body)
                assert data is not None
                assert data.get("pandaReaction") is None or "pandaReaction" not in data
