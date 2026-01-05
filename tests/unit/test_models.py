"""
Unit тесты для моделей базы данных
"""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, ChatHistory, User


class TestModels:
    """Тесты для моделей базы данных"""

    @pytest.fixture
    def test_db_session(self):
        """Фикстура для тестовой базы данных"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    @pytest.mark.unit
    @pytest.mark.database
    def test_user_creation(self, test_db_session):
        """Тест создания пользователя"""
        user = User(
            telegram_id=12345,
            first_name="Тест",
            last_name="Пользователь",
            username="testuser",
            user_type="child",
            age=12,
            grade=6,
        )

        test_db_session.add(user)
        test_db_session.commit()

        assert user.telegram_id == 12345
        assert user.first_name == "Тест"
        assert user.last_name == "Пользователь"
        assert user.username == "testuser"
        assert user.user_type == "child"
        assert user.age == 12
        assert user.grade == 6
        assert user.created_at is not None
        # updated_at не существует в модели User

    @pytest.mark.unit
    @pytest.mark.database
    def test_user_defaults(self, test_db_session):
        """Тест значений по умолчанию для пользователя"""
        user = User(telegram_id=54321, first_name="Минимум")

        test_db_session.add(user)
        test_db_session.commit()

        assert user.telegram_id == 54321
        assert user.first_name == "Минимум"
        assert user.last_name is None
        assert user.username is None
        assert user.user_type == "child"  # значение по умолчанию
        assert user.age is None
        assert user.grade is None
        assert user.is_active is True  # значение по умолчанию
        assert user.parent_telegram_id is None

    @pytest.mark.unit
    @pytest.mark.database
    def test_user_timestamps(self, test_db_session):
        """Тест временных меток пользователя"""
        user = User(telegram_id=99999, first_name="Время")

        test_db_session.add(user)
        test_db_session.commit()

        assert isinstance(user.created_at, datetime)
        # updated_at не существует в модели User
        assert user.created_at <= datetime.utcnow()

    @pytest.mark.unit
    @pytest.mark.database
    def test_chat_history_creation(self, test_db_session):
        """Тест создания истории чата"""
        # Сначала создаем пользователя
        user = User(telegram_id=12345, first_name="Тест")
        test_db_session.add(user)
        test_db_session.commit()

        # Создаем запись истории чата
        chat_history = ChatHistory(
            user_telegram_id=12345, message_text="Привет, как дела?", message_type="user"
        )

        test_db_session.add(chat_history)
        test_db_session.commit()

        assert chat_history.user_telegram_id == 12345
        assert chat_history.message_text == "Привет, как дела?"
        assert chat_history.message_type == "user"
        assert chat_history.timestamp is not None
        assert isinstance(chat_history.timestamp, datetime)

    @pytest.mark.unit
    @pytest.mark.database
    def test_chat_history_types(self, test_db_session):
        """Тест различных типов сообщений в истории чата"""
        user = User(telegram_id=11111, first_name="Типы")
        test_db_session.add(user)
        test_db_session.commit()

        # Создаем записи истории разных типов
        user_msg = ChatHistory(
            user_telegram_id=11111, message_text="Вопрос от пользователя", message_type="user"
        )

        ai_msg = ChatHistory(user_telegram_id=11111, message_text="Ответ от ИИ", message_type="ai")

        test_db_session.add_all([user_msg, ai_msg])
        test_db_session.commit()

        assert user_msg.message_type == "user"
        assert ai_msg.message_type == "ai"

    @pytest.mark.unit
    @pytest.mark.database
    def test_user_relationships(self, test_db_session):
        """Тест связей между пользователями"""
        # Создаем родителя и ребенка
        parent = User(telegram_id=11111, first_name="Родитель", user_type="parent")

        child = User(
            telegram_id=22222, first_name="Ребенок", user_type="child", parent_telegram_id=11111
        )

        test_db_session.add_all([parent, child])
        test_db_session.commit()

        # Проверяем связь
        assert child.parent_telegram_id == 11111
        assert parent.telegram_id == 11111

    @pytest.mark.unit
    @pytest.mark.database
    def test_user_string_representation(self, test_db_session):
        """Тест строкового представления пользователя"""
        user = User(
            telegram_id=12345, first_name="Тест", last_name="Пользователь", username="testuser"
        )

        test_db_session.add(user)
        test_db_session.commit()

        user_str = str(user)
        assert "12345" in user_str
        assert "child" in user_str

    @pytest.mark.unit
    @pytest.mark.database
    def test_chat_history_string_representation(self, test_db_session):
        """Тест строкового представления истории чата"""
        user = User(telegram_id=12345, first_name="Тест")
        test_db_session.add(user)
        test_db_session.commit()

        chat_history = ChatHistory(
            user_telegram_id=12345, message_text="Тестовое сообщение", message_type="user"
        )

        test_db_session.add(chat_history)
        test_db_session.commit()

        history_str = str(chat_history)
        assert "Тестовое сообщение" in history_str
        assert "Тестовое сообщение" in history_str
        assert "user" in history_str

    @pytest.mark.unit
    @pytest.mark.database
    def test_user_validation(self, test_db_session):
        """Тест валидации данных пользователя"""
        # Проверяем обязательные поля
        user = User(telegram_id=12345)  # только обязательное поле

        test_db_session.add(user)
        test_db_session.commit()

        assert user.telegram_id == 12345
        assert user.first_name is None  # может быть None

    @pytest.mark.unit
    @pytest.mark.database
    def test_chat_history_validation(self, test_db_session):
        """Тест валидации данных истории чата"""
        user = User(telegram_id=12345, first_name="Тест")
        test_db_session.add(user)
        test_db_session.commit()

        # Проверяем обязательные поля
        chat_history = ChatHistory(
            user_telegram_id=12345, message_text="Обязательное сообщение", message_type="user"
        )

        test_db_session.add(chat_history)
        test_db_session.commit()

        assert chat_history.user_telegram_id == 12345
        assert chat_history.message_text == "Обязательное сообщение"
        assert chat_history.message_type == "user"

    @pytest.mark.unit
    @pytest.mark.database
    def test_user_all_combinations(self, test_db_session):
        """Тест создания пользователей с разными комбинациями полей"""
        users = [
            User(telegram_id=1),
            User(telegram_id=2, username="user2"),
            User(telegram_id=3, first_name="User3"),
            User(telegram_id=4, last_name="User4"),
            User(telegram_id=5, user_type="child"),
            User(telegram_id=6, age=10),
            User(telegram_id=7, grade=5),
            User(telegram_id=8, username="u8", first_name="F8", last_name="L8"),
            User(telegram_id=9, user_type="parent", age=35),
            User(telegram_id=10, user_type="teacher", age=40),
        ]

        for user in users:
            test_db_session.add(user)
            assert user.telegram_id > 0

        test_db_session.commit()

    @pytest.mark.unit
    @pytest.mark.database
    def test_chat_history_all_types(self, test_db_session):
        """Тест создания истории чата с разными типами сообщений"""
        user = User(telegram_id=11111, first_name="Типы")
        test_db_session.add(user)
        test_db_session.commit()

        for msg_type in ["user", "bot", "system"]:
            h = ChatHistory(
                user_telegram_id=11111, message_text=f"Test {msg_type}", message_type=msg_type
            )
            test_db_session.add(h)
            assert h.message_type == msg_type

        test_db_session.commit()

    @pytest.mark.unit
    @pytest.mark.database
    def test_user_different_ages(self, test_db_session):
        """Тест создания пользователей с разными возрастами"""
        for age in [5, 8, 10, 12, 15, 18, 25, 35, 50]:
            user = User(telegram_id=age * 1000, age=age)
            test_db_session.add(user)
            assert user.age == age

        test_db_session.commit()

    @pytest.mark.unit
    @pytest.mark.database
    def test_user_different_grades(self, test_db_session):
        """Тест создания пользователей с разными классами"""
        for grade in range(1, 12):
            user = User(telegram_id=grade * 10000, grade=grade)
            test_db_session.add(user)
            assert user.grade == grade

        test_db_session.commit()
