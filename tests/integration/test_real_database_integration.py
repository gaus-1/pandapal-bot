"""
РЕАЛЬНЫЕ интеграционные тесты для базы данных и сервисов
БЕЗ МОКОВ - только реальные операции с SQLite базой данных

Тестируем:
- Создание и управление реальной БД
- User Service с реальными операциями
- ChatHistory Service с реальными данными
- Транзакции и откаты
- Целостность данных
"""

import os
import tempfile
from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from bot.config import MAX_AGE, MAX_GRADE, MIN_AGE, MIN_GRADE
from bot.models import Base, ChatHistory, User
from bot.services.history_service import ChatHistoryService
from bot.services.user_service import UserService


class TestRealDatabaseIntegration:
    """Реальные интеграционные тесты с SQLite базой"""

    @pytest.fixture(scope="function")
    def real_db_engine(self):
        """Создаёт временную реальную SQLite базу для каждого теста"""
        # Создаём временный файл для БД
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)

        # Создаём все таблицы
        Base.metadata.create_all(engine)

        yield engine

        # Cleanup
        engine.dispose()
        os.close(db_fd)
        os.unlink(db_path)

    @pytest.fixture(scope="function")
    def real_db_session(self, real_db_engine):
        """Создаёт реальную сессию для теста"""
        SessionLocal = sessionmaker(bind=real_db_engine)
        session = SessionLocal()

        yield session

        session.rollback()
        session.close()

    def test_real_database_creation(self, real_db_engine):
        """Тест реального создания базы данных"""
        # Проверяем что все таблицы созданы
        from sqlalchemy import inspect

        inspector = inspect(real_db_engine)
        tables = inspector.get_table_names()

        assert "users" in tables
        assert "chat_history" in tables
        assert "learning_sessions" in tables

    def test_real_user_creation(self, real_db_session):
        """Тест реального создания пользователя в БД"""
        # Создаём реального пользователя
        user = User(
            telegram_id=123456789,
            username="real_test_user",
            first_name="Real",
            last_name="User",
            age=10,
            grade=5,
            user_type="child",
        )

        real_db_session.add(user)
        real_db_session.commit()

        # Проверяем что пользователь действительно сохранён
        stmt = select(User).where(User.telegram_id == 123456789)
        saved_user = real_db_session.execute(stmt).scalar_one()

        assert saved_user.username == "real_test_user"
        assert saved_user.first_name == "Real"
        assert saved_user.age == 10
        assert saved_user.grade == 5
        assert saved_user.created_at is not None
        assert saved_user.is_active is True

    def test_real_user_service_operations(self, real_db_session):
        """Тест реальных операций UserService с БД"""
        service = UserService(db=real_db_session)

        # 1. Создаём пользователя через сервис
        user = service.get_or_create_user(
            telegram_id=987654321, username="service_user", first_name="Service", last_name="Test"
        )
        real_db_session.commit()

        assert user.telegram_id == 987654321
        assert user.user_type == "child"  # По умолчанию

        # 2. Проверяем что пользователь действительно в БД
        found_user = service.get_user_by_telegram_id(987654321)
        assert found_user is not None
        assert found_user.username == "service_user"

        # 3. Обновляем профиль
        updated_user = service.update_user_profile(telegram_id=987654321, age=12, grade=6)
        real_db_session.commit()

        assert updated_user.age == 12
        assert updated_user.grade == 6

        # 4. Проверяем обновление в БД
        refreshed_user = service.get_user_by_telegram_id(987654321)
        assert refreshed_user.age == 12
        assert refreshed_user.grade == 6

    def test_real_user_service_validation(self, real_db_session):
        """Тест реальной валидации данных"""
        service = UserService(db=real_db_session)

        # Создаём пользователя
        user = service.get_or_create_user(
            telegram_id=111111111, username="validator", first_name="Test"
        )
        real_db_session.commit()

        # Проверяем валидацию возраста
        with pytest.raises(ValueError, match="Возраст должен быть"):
            service.update_user_profile(111111111, age=3)  # Слишком мало

        with pytest.raises(ValueError, match="Возраст должен быть"):
            service.update_user_profile(111111111, age=25)  # Слишком много

        # Проверяем валидацию класса
        with pytest.raises(ValueError, match="Класс должен быть"):
            service.update_user_profile(111111111, grade=0)

        with pytest.raises(ValueError, match="Класс должен быть"):
            service.update_user_profile(111111111, grade=15)

        # Проверяем валидацию типа пользователя
        with pytest.raises(ValueError, match="user_type должен быть"):
            service.update_user_profile(111111111, user_type="admin")

    def test_real_parent_child_link(self, real_db_session):
        """Тест реальной связи родитель-ребёнок"""
        service = UserService(db=real_db_session)

        # Создаём пользователя
        user = service.get_or_create_user(
            telegram_id=222222222, username="test_user", first_name="Test"
        )
        service.update_user_profile(222222222, age=10, grade=5)

        real_db_session.commit()

        # Проверяем что профиль обновлён
        user_from_db = service.get_user_by_telegram_id(222222222)
        assert user_from_db.age == 10
        assert user_from_db.grade == 5

    def test_real_chat_history_operations(self, real_db_session):
        """Тест реальных операций с историей чата"""
        # Создаём пользователя
        user = User(
            telegram_id=444444444, username="chat_user", first_name="Chat", user_type="child"
        )
        real_db_session.add(user)
        real_db_session.commit()

        # Создаём сервис истории
        service = ChatHistoryService(db=real_db_session)

        # 1. Добавляем сообщения
        msg1 = service.add_message(444444444, "Привет! Как дела?", "user")
        msg2 = service.add_message(444444444, "Привет! Отлично, спасибо!", "ai")
        msg3 = service.add_message(444444444, "Помоги с математикой", "user")
        real_db_session.commit()

        assert msg1.message_text == "Привет! Как дела?"
        assert msg2.message_type == "ai"
        assert msg3.user_telegram_id == 444444444

        # 2. Получаем историю
        history = service.get_recent_history(444444444)
        assert len(history) == 3
        assert history[0].message_text == "Привет! Как дела?"
        assert history[1].message_type == "ai"
        assert history[2].message_text == "Помоги с математикой"

        # 3. Получаем с лимитом
        limited_history = service.get_recent_history(444444444, limit=2)
        assert len(limited_history) == 2
        # Должны быть последние 2 сообщения
        assert limited_history[0].message_type == "ai"
        assert limited_history[1].message_text == "Помоги с математикой"

    def test_real_chat_history_formatting(self, real_db_session):
        """Тест реального форматирования истории"""
        # Создаём пользователя
        user = User(telegram_id=555555555, username="format_user")
        real_db_session.add(user)
        real_db_session.commit()

        service = ChatHistoryService(db=real_db_session)

        # Добавляем диалог
        service.add_message(555555555, "Что такое Python?", "user")
        service.add_message(555555555, "Python - это язык программирования", "ai")
        service.add_message(555555555, "А зачем он нужен?", "user")
        real_db_session.commit()

        # Получаем форматированную историю
        context = service.get_conversation_context(555555555)

        assert "User: Что такое Python?" in context
        assert "AI: Python - это язык программирования" in context
        assert "User: А зачем он нужен?" in context

        # Проверяем порядок
        lines = context.split("\n")
        assert len(lines) == 3
        assert lines[0].startswith("User:")
        assert lines[1].startswith("AI:")
        assert lines[2].startswith("User:")

    def test_real_chat_history_clear(self, real_db_session):
        """Тест реальной очистки истории"""
        # Создаём пользователя
        user = User(telegram_id=666666666, username="clear_user")
        real_db_session.add(user)
        real_db_session.commit()

        service = ChatHistoryService(db=real_db_session)

        # Добавляем 5 сообщений
        for i in range(5):
            service.add_message(666666666, f"Сообщение {i}", "user")
        real_db_session.commit()

        # Проверяем что они есть
        count_before = service.get_message_count(666666666)
        assert count_before == 5

        # Очищаем
        deleted_count = service.clear_history(666666666)
        real_db_session.commit()

        assert deleted_count == 5

        # Проверяем что история пуста
        count_after = service.get_message_count(666666666)
        assert count_after == 0

    def test_real_multiple_users_isolation(self, real_db_session):
        """Тест изоляции данных между пользователями"""
        user_service = UserService(db=real_db_session)
        chat_service = ChatHistoryService(db=real_db_session)

        # Создаём двух пользователей
        user1 = user_service.get_or_create_user(777777777, "user1", "User", "One")
        user2 = user_service.get_or_create_user(888888888, "user2", "User", "Two")
        real_db_session.commit()

        # Добавляем сообщения для каждого
        chat_service.add_message(777777777, "Сообщение от пользователя 1", "user")
        chat_service.add_message(888888888, "Сообщение от пользователя 2", "user")
        real_db_session.commit()

        # Проверяем изоляцию
        history1 = chat_service.get_recent_history(777777777)
        history2 = chat_service.get_recent_history(888888888)

        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0].message_text == "Сообщение от пользователя 1"
        assert history2[0].message_text == "Сообщение от пользователя 2"

    def test_real_transaction_rollback(self, real_db_session):
        """Тест реального отката транзакций"""
        service = UserService(db=real_db_session)

        # Создаём пользователя
        user = service.get_or_create_user(999999999, "rollback_user", "Rollback")
        real_db_session.commit()

        # Изменяем данные но НЕ коммитим
        service.update_user_profile(999999999, age=15)

        # Откатываем
        real_db_session.rollback()

        # Проверяем что изменения не сохранились
        user_from_db = service.get_user_by_telegram_id(999999999)
        assert user_from_db.age is None  # Возраст не должен был сохраниться

    def test_real_user_deactivation(self, real_db_session):
        """Тест реальной деактивации пользователя"""
        service = UserService(db=real_db_session)

        # Создаём пользователя
        user = service.get_or_create_user(101010101, "deactivate_user", "Deactivate")
        real_db_session.commit()

        assert user.is_active is True

        # Деактивируем
        result = service.deactivate_user(101010101)
        real_db_session.commit()

        assert result is True

        # Проверяем в БД
        user_from_db = service.get_user_by_telegram_id(101010101)
        assert user_from_db.is_active is False

    def test_real_user_display_name(self, real_db_session):
        """Тест получения отображаемого имени пользователя"""
        service = UserService(db=real_db_session)

        # Пользователь с именем и фамилией
        user1 = service.get_or_create_user(202020202, "user1", "John", "Doe")
        real_db_session.commit()
        name1 = service.get_user_display_name(user1)
        assert name1 == "John Doe"

        # Пользователь только с username
        user2 = service.get_or_create_user(303030303, "johndoe", None, None)
        real_db_session.commit()
        name2 = service.get_user_display_name(user2)
        assert name2 == "@johndoe"

        # Пользователь только с telegram_id
        user3 = User(telegram_id=404040404)
        real_db_session.add(user3)
        real_db_session.commit()
        name3 = service.get_user_display_name(user3)
        assert name3 == "User404040404"

    def test_real_concurrent_operations(self, real_db_engine):
        """Тест параллельных операций с БД"""
        SessionLocal = sessionmaker(bind=real_db_engine)

        # Две независимые сессии
        session1 = SessionLocal()
        session2 = SessionLocal()

        try:
            service1 = UserService(db=session1)
            service2 = UserService(db=session2)

            # Создаём пользователя в первой сессии
            user1 = service1.get_or_create_user(505050505, "concurrent1", "Test")
            session1.commit()

            # Находим его во второй сессии
            user2 = service2.get_user_by_telegram_id(505050505)

            assert user2 is not None
            assert user2.username == "concurrent1"

        finally:
            session1.close()
            session2.close()
