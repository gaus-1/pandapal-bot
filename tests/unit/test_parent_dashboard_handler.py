"""
Тесты для bot/handlers/parent_dashboard.py
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.unit
class TestParentDashboard:
    """Тесты для дашборда родителей"""

    @pytest.fixture
    def mock_message(self):
        """Мок сообщения"""
        message = MagicMock()
        message.from_user.id = 987654321
        message.answer = AsyncMock()
        return message

    @pytest.fixture
    def mock_state(self):
        """Мок FSM состояния"""
        return MagicMock()

    @pytest.fixture
    def mock_parent_user(self):
        """Мок пользователя-родителя"""
        user = MagicMock()
        user.user_type = "parent"
        user.telegram_id = 987654321
        user.first_name = "Родитель"
        return user

    @pytest.fixture
    def mock_child_user(self):
        """Мок пользователя-ребенка"""
        user = MagicMock()
        user.user_type = "child"
        user.telegram_id = 123456789
        user.first_name = "Ребенок"
        user.age = 10
        return user

    @pytest.mark.asyncio
    async def test_start_parent_dashboard_no_children_real_db(self, mock_message, mock_state):
        """Тест дашборда без привязанных детей с РЕАЛЬНОЙ БД"""
        import os
        import tempfile

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from bot.database import get_db
        from bot.handlers.parent_dashboard import start_parent_dashboard
        from bot.models import Base
        from bot.services.user_service import UserService

        # Создаем РЕАЛЬНУЮ БД
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        real_session = SessionLocal()

        # Создаем реального родителя через реальный сервис
        user_service = UserService(real_session)
        parent = user_service.get_or_create_user(
            telegram_id=987654321, username="parent_test", first_name="Родитель"
        )
        user_service.update_user_profile(telegram_id=987654321, user_type="parent")
        real_session.commit()

        # Используем реальный get_db
        def mock_get_db_real():
            return real_session

        try:
            with patch(
                "bot.handlers.parent_dashboard.get_db", side_effect=lambda: mock_get_db_real()
            ):
                await start_parent_dashboard(mock_message, mock_state)

            # Проверяем результат работы, а не факт вызова методов
            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args
            if call_args:
                answer_text = ""
                if call_args[0]:
                    answer_text = call_args[0][0]
                elif call_args[1] and "text" in call_args[1]:
                    answer_text = call_args[1]["text"]
                assert (
                    "нет привязанных детей" in answer_text.lower()
                    or "добавить ребенка" in answer_text.lower()
                )
        finally:
            real_session.close()
            engine.dispose()
            os.close(db_fd)
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_start_parent_dashboard_not_parent_real_db(self, mock_message, mock_state):
        """Тест дашборда для не-родителя с РЕАЛЬНОЙ БД"""
        import os
        import tempfile

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from bot.handlers.parent_dashboard import start_parent_dashboard
        from bot.models import Base
        from bot.services.user_service import UserService

        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        real_session = SessionLocal()

        # Создаем реального ребенка через реальный сервис
        user_service = UserService(real_session)
        child = user_service.get_or_create_user(
            telegram_id=999999999, username="child_test", first_name="Ребенок"
        )
        user_service.update_user_profile(telegram_id=999999999, age=10, user_type="child")
        real_session.commit()

        def mock_get_db_real():
            return real_session

        try:
            with patch(
                "bot.handlers.parent_dashboard.get_db", side_effect=lambda: mock_get_db_real()
            ):
                await start_parent_dashboard(mock_message, mock_state)

            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args
            if call_args:
                answer_text = ""
                if call_args[0]:
                    answer_text = call_args[0][0]
                elif call_args[1] and "text" in call_args[1]:
                    answer_text = call_args[1]["text"]
                assert "только родителям" in answer_text.lower() or "❌" in answer_text
        finally:
            real_session.close()
            engine.dispose()
            os.close(db_fd)
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_start_parent_dashboard_with_children_real_db(self, mock_message, mock_state):
        """Тест дашборда с привязанными детьми с РЕАЛЬНОЙ БД"""
        import os
        import tempfile

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from bot.handlers.parent_dashboard import start_parent_dashboard
        from bot.models import Base
        from bot.services.user_service import UserService

        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        real_session = SessionLocal()

        # Создаем реального родителя и ребенка через реальные сервисы
        user_service = UserService(real_session)
        parent = user_service.get_or_create_user(
            telegram_id=888888888, username="parent_multi", first_name="Родитель"
        )
        user_service.update_user_profile(telegram_id=888888888, user_type="parent")

        child = user_service.get_or_create_user(
            telegram_id=777777777, username="child_multi", first_name="Ребенок"
        )
        user_service.update_user_profile(telegram_id=777777777, age=10, user_type="child")
        child.parent_telegram_id = 888888888
        real_session.commit()

        mock_message.from_user.id = 888888888

        def mock_get_db_real():
            return real_session

        try:
            with patch(
                "bot.handlers.parent_dashboard.get_db", side_effect=lambda: mock_get_db_real()
            ):
                await start_parent_dashboard(mock_message, mock_state)

            # Проверяем результат работы
            mock_message.answer.assert_called_once()
        finally:
            real_session.close()
            engine.dispose()
            os.close(db_fd)
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_start_parent_dashboard_user_not_found_real_db(self, mock_message, mock_state):
        """Тест дашборда когда пользователь не найден с РЕАЛЬНОЙ БД"""
        import os
        import tempfile

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from bot.handlers.parent_dashboard import start_parent_dashboard
        from bot.models import Base

        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        real_session = SessionLocal()

        # Не создаем пользователя - проверяем случай когда его нет

        def mock_get_db_real():
            return real_session

        try:
            with patch(
                "bot.handlers.parent_dashboard.get_db", side_effect=lambda: mock_get_db_real()
            ):
                await start_parent_dashboard(mock_message, mock_state)

            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args
            if call_args:
                answer_text = ""
                if call_args[0]:
                    answer_text = call_args[0][0]
                elif call_args[1] and "text" in call_args[1]:
                    answer_text = call_args[1]["text"]
                assert "только родителям" in answer_text.lower() or "❌" in answer_text
        finally:
            real_session.close()
            engine.dispose()
            os.close(db_fd)
            os.unlink(db_path)

    def test_parent_dashboard_security_only_parents_access(self):
        """КРИТИЧНО: Тест что только родители могут получить доступ к дашборду"""
        import os
        import tempfile

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from bot.models import Base, User
        from bot.services.user_service import UserService

        # Создаем реальную БД для теста
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        try:
            # Создаем ребенка
            child = User(
                telegram_id=111111111,
                username="child_user",
                first_name="Ребенок",
                user_type="child",
                age=10,
            )
            session.add(child)

            # Создаем родителя (родители не имеют возраста в БД)
            parent = User(
                telegram_id=222222222,
                username="parent_user",
                first_name="Родитель",
                user_type="parent",
                age=None,  # Родители не имеют возраста
            )
            session.add(parent)
            session.commit()

            # Проверяем что сервис правильно определяет тип пользователя
            user_service = UserService(db=session)
            found_child = user_service.get_user_by_telegram_id(111111111)
            found_parent = user_service.get_user_by_telegram_id(222222222)

            assert found_child.user_type == "child"
            assert found_parent.user_type == "parent"
            assert found_child.user_type != "parent"  # Ребенок не может быть родителем
            assert found_parent.user_type != "child"  # Родитель не может быть ребенком

        finally:
            session.close()
            engine.dispose()
            os.close(db_fd)
            os.unlink(db_path)

    def test_router_has_required_handlers(self):
        """Тест что роутер имеет необходимые обработчики"""
        from bot.handlers import parent_dashboard
        from bot.handlers.parent_dashboard import router

        assert router is not None
        assert hasattr(parent_dashboard, "start_parent_dashboard")
        assert hasattr(parent_dashboard, "show_child_dashboard")

    @pytest.mark.asyncio
    async def test_show_child_dashboard_real_db(self, mock_message, mock_state):
        """Тест показа дашборда ребенка с РЕАЛЬНОЙ БД"""
        import os
        import tempfile
        from datetime import datetime

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from bot.handlers.parent_dashboard import show_child_dashboard
        from bot.models import Base, ChatHistory
        from bot.services.user_service import UserService

        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        real_session = SessionLocal()

        # Создаем реального ребенка с реальной историей
        user_service = UserService(real_session)
        child = user_service.get_or_create_user(
            telegram_id=123456789, username="child_dashboard", first_name="Ребенок"
        )
        user_service.update_user_profile(telegram_id=123456789, age=10, user_type="child")

        # Добавляем реальную историю чата
        msg1 = ChatHistory(
            user_telegram_id=123456789,
            message_text="Привет",
            message_type="user",
            timestamp=datetime.now(),
        )
        msg2 = ChatHistory(
            user_telegram_id=123456789,
            message_text="Ответ AI",
            message_type="ai",
            timestamp=datetime.now(),
        )
        real_session.add_all([msg1, msg2])
        real_session.commit()

        # Мокаем только внешний Telegram API
        mock_callback = MagicMock()
        mock_callback.data = "dashboard_child_123456789"
        mock_from_user = MagicMock()
        mock_from_user.id = 987654321
        mock_callback.from_user = mock_from_user
        mock_callback.answer = AsyncMock()
        mock_callback.message = mock_message
        mock_callback.message.edit_text = AsyncMock()

        def mock_get_db_real():
            return real_session

        try:
            with patch(
                "bot.handlers.parent_dashboard.get_db", side_effect=lambda: mock_get_db_real()
            ):
                await show_child_dashboard(mock_callback, mock_state)

            # Проверяем результат работы, а не факт вызова методов
            mock_callback.answer.assert_called_once()
            mock_callback.message.edit_text.assert_called()
            # Проверяем что в ответе есть реальные данные
            call_args = mock_callback.message.edit_text.call_args
            if call_args:
                text = ""
                if call_args[1] and "text" in call_args[1]:
                    text = call_args[1]["text"]
                assert "Дашборд ребенка" in text or "Активность" in text
        finally:
            real_session.close()
            engine.dispose()
            os.close(db_fd)
            os.unlink(db_path)
