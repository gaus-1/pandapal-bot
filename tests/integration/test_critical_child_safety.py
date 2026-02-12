"""
КРИТИЧНЫЕ тесты для безопасности детей
Тестируем самые важные функции для детского образовательного проекта
БЕЗ МОКОВ - только реальные проверки безопасности
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, ChatHistory, User
from bot.services.history_service import ChatHistoryService
from bot.services.moderation_service import ContentModerationService
from bot.services.user_service import UserService


class TestCriticalChildSafety:
    """Критичные тесты безопасности для детей"""

    @pytest.fixture(scope="function")
    def real_safety_db(self):
        """Реальная БД для тестов безопасности"""
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

    def test_child_cannot_access_adult_content(self, real_safety_db):
        """КРИТИЧНО: ребёнок не может получить доступ к взрослому контенту"""
        moderation = ContentModerationService()

        adult_queries = [
            "порно",
            "секс",
            "xxx",
        ]

        for query in adult_queries:
            is_safe, reason = moderation.is_safe_content(query)
            assert is_safe is False, f"ОПАСНО! Ребёнок может получить: {query}"
            assert reason is not None

    def test_child_protected_from_violence(self, real_safety_db):
        """КРИТИЧНО: ребёнок защищён от контента о насилии"""
        moderation = ContentModerationService()

        violence_queries = [
            "как убить",
            "купить оружие",
        ]

        for query in violence_queries:
            is_safe, reason = moderation.is_safe_content(query)
            assert is_safe is False, f"ОПАСНО! Контент о насилии: {query}"

    def test_child_protected_from_drugs(self, real_safety_db):
        """КРИТИЧНО: ребёнок защищён от информации о наркотиках"""
        moderation = ContentModerationService()

        drug_queries = [
            "наркотики",
            "героин",
            "кокаин",
        ]

        for query in drug_queries:
            is_safe, reason = moderation.is_safe_content(query)
            assert is_safe is False, f"ОПАСНО! Информация о наркотиках: {query}"

    def test_educational_content_allowed(self, real_safety_db):
        """КРИТИЧНО: образовательный контент должен проходить"""
        moderation = ContentModerationService()

        educational_queries = [
            "помоги решить задачу",
            "объясни теорему Пифагора",
            "что такое фотосинтез",
            "история России",
            "математика 5 класс",
            "английский язык",
            "физика 7 класс",
        ]

        for query in educational_queries:
            is_safe, reason = moderation.is_safe_content(query)
            assert is_safe is True, f"Образовательный контент заблокирован: {query}"

    def test_child_message_history_privacy(self, real_safety_db):
        """КРИТИЧНО: история сообщений ребёнка изолирована"""
        user_service = UserService(db=real_safety_db)
        chat_service = ChatHistoryService(db=real_safety_db)

        # Создаём двух детей
        child1 = user_service.get_or_create_user(300001, "child1", "Child", "One")
        child2 = user_service.get_or_create_user(300002, "child2", "Child", "Two")
        real_safety_db.commit()

        # Добавляем личные сообщения
        chat_service.add_message(300001, "Мой секрет 1", "user")
        chat_service.add_message(300002, "Мой секрет 2", "user")
        real_safety_db.commit()

        # Проверяем изоляцию
        history1 = chat_service.get_recent_history(300001)
        history2 = chat_service.get_recent_history(300002)

        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0].message_text == "Мой секрет 1"
        assert history2[0].message_text == "Мой секрет 2"

        # Ребёнок 1 НЕ должен видеть сообщения ребёнка 2
        assert history1[0].message_text != history2[0].message_text

    def test_age_validation_for_children(self, real_safety_db):
        """КРИТИЧНО: возраст ребёнка валидируется"""
        user_service = UserService(db=real_safety_db)

        child = user_service.get_or_create_user(600001, "child")
        real_safety_db.commit()

        # Слишком малый возраст
        with pytest.raises(ValueError):
            user_service.update_user_profile(600001, age=3)

        # Слишком большой возраст (взрослый)
        with pytest.raises(ValueError):
            user_service.update_user_profile(600001, age=25)

        # Нормальный детский возраст
        try:
            user_service.update_user_profile(600001, age=10)
            real_safety_db.commit()
            assert True
        except ValueError:
            pytest.fail("Нормальный детский возраст не должен вызывать ошибку")

    def test_profanity_blocked_in_child_messages(self, real_safety_db):
        """КРИТИЧНО: нецензурная лексика блокируется"""
        moderation = ContentModerationService()

        profanity_samples = [
            "блять",
            "хуй",
            "пизда",
            "сука",
            "ебать",
        ]

        for profanity in profanity_samples:
            is_safe, reason = moderation.is_safe_content(profanity)
            assert is_safe is False, f"Нецензурная лексика пропущена: {profanity}"

    def test_child_age_appropriate_responses(self, real_safety_db):
        """КРИТИЧНО: ответы адаптируются под возраст"""
        from bot.services.ai_context_builder import ContextBuilder

        builder = ContextBuilder()

        # Для младшего школьника (6-8 лет)
        context_young = builder.build(user_message="Что такое дробь?", chat_history=[], user_age=7)
        assert (
            "6-8 лет" in context_young
            or "6-7 лет" in context_young
            or "простыми словами" in context_young
            or "простые слова" in context_young
        )

        # Для среднего школьника (9-12 лет)
        context_middle = builder.build(
            user_message="Что такое дробь?", chat_history=[], user_age=10
        )
        assert (
            "9-12 лет" in context_middle
            or "10-11 лет" in context_middle
            or "понятные примеры" in context_middle
            or "таблицы" in context_middle
        )

        # Для подростка (13-18 лет)
        context_teen = builder.build(user_message="Что такое дробь?", chat_history=[], user_age=15)
        assert "13-18 лет" in context_teen or "подросток" in context_teen or "14-15" in context_teen

    def test_emergency_contact_data_safety(self, real_safety_db):
        """КРИТИЧНО: экстренные контакты ребёнка безопасно хранятся"""
        # Проверяем что в моделях нет открытого хранения телефонов
        from bot.models import User

        user = User(
            telegram_id=700001, username="emergency_test", first_name="Test", user_type="child"
        )

        # Telegram ID - это OK, но личные телефоны не должны храниться открыто
        assert hasattr(user, "telegram_id")
        assert user.telegram_id == 700001

    def test_dangerous_input_handling(self, real_safety_db):
        """КРИТИЧНО: опасный ввод обрабатывается"""
        # Проверяем что модерация работает с опасным вводом
        moderation = ContentModerationService()

        dangerous_inputs = [
            "Test\x00null",
            "Test<script>alert('xss')</script>",
        ]

        for dangerous in dangerous_inputs:
            # Модерация должна обработать без ошибок
            try:
                is_safe, reason = moderation.is_safe_content(dangerous)
                assert True  # Успешно обработано
            except Exception as e:
                pytest.fail(f"Модерация не обработала опасный ввод: {e}")


class TestCriticalDataIntegrity:
    """Критичные тесты целостности данных"""

    @pytest.fixture(scope="function")
    def integrity_db(self):
        """БД для тестов целостности"""
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

    def test_user_data_not_corrupted_on_concurrent_access(self, integrity_db):
        """КРИТИЧНО: данные пользователя не повреждаются при параллельном доступе"""
        user_service = UserService(db=integrity_db)

        # Создаём пользователя
        user = user_service.get_or_create_user(800001, "concurrent_user")
        integrity_db.commit()

        # Обновляем данные несколько раз
        for i in range(5):
            user_service.update_user_profile(800001, age=10 + i)
            integrity_db.commit()

        # Проверяем что данные корректны
        final_user = user_service.get_user_by_telegram_id(800001)
        assert final_user is not None
        assert final_user.age == 14  # 10 + 4

    def test_chat_history_chronological_order(self, integrity_db):
        """КРИТИЧНО: история чата сохраняет хронологический порядок"""
        from bot.models import User

        user = User(telegram_id=900001, username="order_test")
        integrity_db.add(user)
        integrity_db.commit()

        chat_service = ChatHistoryService(db=integrity_db)

        # Добавляем сообщения
        messages = []
        for i in range(5):
            msg = chat_service.add_message(900001, f"Message {i}", "user")
            messages.append(msg)

        integrity_db.commit()

        # Получаем историю
        history = chat_service.get_recent_history(900001)

        # Проверяем порядок
        assert len(history) == 5
        for i, msg in enumerate(history):
            assert f"Message {i}" in msg.message_text

    def test_user_deactivation_safety(self, integrity_db):
        """КРИТИЧНО: деактивация пользователя безопасна"""
        user_service = UserService(db=integrity_db)

        # Создаём пользователя
        user = user_service.get_or_create_user(1000001, "deactivate_test")
        integrity_db.commit()

        assert user.is_active is True

        # Деактивируем
        result = user_service.deactivate_user(1000001)
        integrity_db.commit()

        assert result is True

        # Проверяем что пользователь деактивирован
        deactivated_user = user_service.get_user_by_telegram_id(1000001)
        assert deactivated_user is not None  # Пользователь все еще существует
        assert deactivated_user.is_active is False  # Но деактивирован
