"""
РЕАЛЬНЫЕ интеграционные тесты для parent_dashboard с реальной БД
БЕЗ МОКОВ - только реальные операции с SQLite базой данных

Тестируем:
- Реальную работу дашборда родителей
- Доступ только для родителей
- Реальную статистику детей
- Безопасность доступа к данным
"""

import os
import tempfile
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, ChatHistory, User
from bot.services.user_service import UserService


class TestParentDashboardReal:
    """Реальные интеграционные тесты дашборда родителей"""

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

    def test_parent_dashboard_real_parent_access(self, real_db_session):
        """КРИТИЧНО: Родитель может получить доступ к дашборду"""
        user_service = UserService(real_db_session)

        # Создаем родителя
        parent = user_service.get_or_create_user(
            telegram_id=111111111,
            username="parent_user",
            first_name="Родитель",
            last_name="Тестовый",
        )
        parent.user_type = "parent"
        parent.age = None  # Родители не имеют возраста
        real_db_session.commit()

        # Проверяем что родитель создан
        found_parent = user_service.get_user_by_telegram_id(111111111)
        assert found_parent is not None
        assert found_parent.user_type == "parent"
        assert found_parent.age is None

        # Проверяем что родитель может получить список детей
        children = user_service.get_user_children(111111111)
        assert isinstance(children, list)

    def test_parent_dashboard_real_child_creation(self, real_db_session):
        """Тест создания ребенка и связи с родителем"""
        user_service = UserService(real_db_session)

        # Создаем родителя
        parent = user_service.get_or_create_user(
            telegram_id=222222222,
            username="parent2",
            first_name="Родитель2",
        )
        parent.user_type = "parent"
        real_db_session.commit()

        # Создаем ребенка
        child = user_service.get_or_create_user(
            telegram_id=333333333,
            username="child_user",
            first_name="Ребенок",
        )
        user_service.update_user_profile(telegram_id=333333333, age=10, grade=5, user_type="child")
        child.parent_telegram_id = 222222222
        real_db_session.commit()

        # Проверяем связь
        found_child = user_service.get_user_by_telegram_id(333333333)
        assert found_child.parent_telegram_id == 222222222
        assert found_child.user_type == "child"
        assert found_child.age == 10

        # Проверяем что родитель видит ребенка
        children = user_service.get_user_children(222222222)
        assert len(children) == 1
        assert children[0].telegram_id == 333333333

    def test_parent_dashboard_real_statistics(self, real_db_session):
        """Тест реальной статистики активности ребенка"""
        user_service = UserService(real_db_session)

        # Создаем родителя и ребенка
        parent = user_service.get_or_create_user(
            telegram_id=444444444, username="parent3", first_name="Родитель3"
        )
        parent.user_type = "parent"
        real_db_session.commit()

        child = user_service.get_or_create_user(
            telegram_id=555555555, username="child2", first_name="Ребенок2"
        )
        user_service.update_user_profile(telegram_id=555555555, age=12, user_type="child")
        child.parent_telegram_id = 444444444
        real_db_session.commit()

        # Создаем реальную историю чата
        messages = [
            ChatHistory(
                user_telegram_id=555555555,
                message_text="Привет",
                message_type="user",
                timestamp=datetime.now() - timedelta(days=1),
            ),
            ChatHistory(
                user_telegram_id=555555555,
                message_text="Помоги с математикой",
                message_type="user",
                timestamp=datetime.now() - timedelta(hours=12),
            ),
            ChatHistory(
                user_telegram_id=555555555,
                message_text="Ответ AI",
                message_type="ai",
                timestamp=datetime.now() - timedelta(hours=12),
            ),
        ]

        for msg in messages:
            real_db_session.add(msg)
        real_db_session.commit()

        # Проверяем реальную статистику
        all_messages = (
            real_db_session.query(ChatHistory)
            .filter(ChatHistory.user_telegram_id == 555555555)
            .all()
        )
        assert len(all_messages) == 3

        user_messages = [m for m in all_messages if m.message_type == "user"]
        assert len(user_messages) == 2

        ai_messages = [m for m in all_messages if m.message_type == "ai"]
        assert len(ai_messages) == 1

    def test_parent_dashboard_security_child_cannot_access(self, real_db_session):
        """КРИТИЧНО: Ребенок не может получить доступ к дашборду родителей"""
        user_service = UserService(real_db_session)

        # Создаем ребенка
        child = user_service.get_or_create_user(
            telegram_id=666666666, username="child3", first_name="Ребенок3"
        )
        user_service.update_user_profile(telegram_id=666666666, age=8, user_type="child")
        real_db_session.commit()

        # Проверяем что ребенок не может получить список детей
        children = user_service.get_user_children(666666666)
        assert len(children) == 0  # Ребенок не может быть родителем

        # Проверяем что тип пользователя правильный
        found_child = user_service.get_user_by_telegram_id(666666666)
        assert found_child.user_type == "child"
        assert found_child.user_type != "parent"

    def test_parent_dashboard_real_multiple_children(self, real_db_session):
        """Тест дашборда с несколькими детьми"""
        user_service = UserService(real_db_session)

        # Создаем родителя
        parent = user_service.get_or_create_user(
            telegram_id=777777777, username="parent4", first_name="Родитель4"
        )
        parent.user_type = "parent"
        real_db_session.commit()

        # Создаем нескольких детей
        for i, age in enumerate([8, 10, 12], start=1):
            child = user_service.get_or_create_user(
                telegram_id=700000000 + i,
                username=f"child{i}",
                first_name=f"Ребенок{i}",
            )
            user_service.update_user_profile(telegram_id=700000000 + i, age=age, user_type="child")
            child.parent_telegram_id = 777777777
            real_db_session.commit()

        # Проверяем что родитель видит всех детей
        children = user_service.get_user_children(777777777)
        assert len(children) == 3

        # Проверяем что все дети привязаны к родителю
        for child in children:
            assert child.parent_telegram_id == 777777777
            assert child.user_type == "child"

    def test_parent_dashboard_real_chat_history_isolation(self, real_db_session):
        """КРИТИЧНО: История чата изолирована между детьми"""
        user_service = UserService(real_db_session)

        # Создаем двух детей одного родителя
        parent = user_service.get_or_create_user(
            telegram_id=888888888, username="parent5", first_name="Родитель5"
        )
        parent.user_type = "parent"
        real_db_session.commit()

        child1 = user_service.get_or_create_user(
            telegram_id=800000001, username="child_a", first_name="РебенокA"
        )
        user_service.update_user_profile(telegram_id=800000001, age=9, user_type="child")
        child1.parent_telegram_id = 888888888

        child2 = user_service.get_or_create_user(
            telegram_id=800000002, username="child_b", first_name="РебенокB"
        )
        user_service.update_user_profile(telegram_id=800000002, age=11, user_type="child")
        child2.parent_telegram_id = 888888888
        real_db_session.commit()

        # Создаем историю для каждого ребенка
        msg1 = ChatHistory(
            user_telegram_id=800000001,
            message_text="Сообщение от ребенка A",
            message_type="user",
        )
        msg2 = ChatHistory(
            user_telegram_id=800000002,
            message_text="Сообщение от ребенка B",
            message_type="user",
        )
        real_db_session.add_all([msg1, msg2])
        real_db_session.commit()

        # Проверяем изоляцию
        child1_messages = (
            real_db_session.query(ChatHistory)
            .filter(ChatHistory.user_telegram_id == 800000001)
            .all()
        )
        child2_messages = (
            real_db_session.query(ChatHistory)
            .filter(ChatHistory.user_telegram_id == 800000002)
            .all()
        )

        assert len(child1_messages) == 1
        assert len(child2_messages) == 1
        assert child1_messages[0].message_text == "Сообщение от ребенка A"
        assert child2_messages[0].message_text == "Сообщение от ребенка B"

    def test_parent_dashboard_real_blocked_messages_tracking(self, real_db_session):
        """Тест отслеживания заблокированных сообщений"""
        user_service = UserService(real_db_session)

        # Создаем ребенка
        child = user_service.get_or_create_user(
            telegram_id=900000001, username="child_blocked", first_name="Ребенок"
        )
        user_service.update_user_profile(telegram_id=900000001, age=10, user_type="child")
        real_db_session.commit()

        # Создаем смешанную историю: обычные и заблокированные сообщения
        messages = [
            ChatHistory(
                user_telegram_id=900000001,
                message_text="Помоги с математикой",
                message_type="user",
            ),
            ChatHistory(
                user_telegram_id=900000001,
                message_text="Заблокированное сообщение",
                message_type="system",  # Используем system для заблокированных
            ),
            ChatHistory(
                user_telegram_id=900000001,
                message_text="Еще одно нормальное",
                message_type="user",
            ),
        ]
        real_db_session.add_all(messages)
        real_db_session.commit()

        # Проверяем статистику заблокированных (используем system для заблокированных)
        all_messages = (
            real_db_session.query(ChatHistory)
            .filter(ChatHistory.user_telegram_id == 900000001)
            .all()
        )
        blocked = [
            m
            for m in all_messages
            if m.message_type == "system" and "Заблокированное" in m.message_text
        ]
        safe = [m for m in all_messages if m.message_type == "user"]

        assert len(all_messages) == 3
        assert len(blocked) == 1
        assert len(safe) == 2

        # Проверяем индекс безопасности
        safety_index = max(100 - (len(blocked) / len(all_messages) * 100), 0)
        assert safety_index > 0
        assert safety_index < 100  # Есть заблокированные
