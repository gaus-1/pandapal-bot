"""
Дополнительные РЕАЛЬНЫЕ интеграционные тесты для повышения покрытия
Фокус на модулях с низким покрытием без использования моков
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base


class TestRealDatabaseExtended:
    """Расширенные реальные тесты базы данных"""

    @pytest.fixture(scope="function")
    def real_db_setup(self):
        """Реальная БД для расширенных тестов"""
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        yield session, engine

        session.close()
        engine.dispose()
        os.close(db_fd)
        os.unlink(db_path)

    def test_real_user_progress_tracking(self, real_db_setup):
        """Тест реального отслеживания прогресса пользователя"""
        from bot.models import User, UserProgress

        session, _ = real_db_setup

        # Создаём пользователя
        user = User(
            telegram_id=100001,
            username="progress_user",
            first_name="Progress",
            user_type="child",
            age=12,
            grade=6,
        )
        session.add(user)
        session.commit()

        # Добавляем прогресс
        progress = UserProgress(user_telegram_id=100001, subject="математика", level=5, points=850)
        session.add(progress)
        session.commit()

        # Проверяем
        assert progress.user_telegram_id == 100001
        assert progress.subject == "математика"
        assert progress.level == 5
        assert progress.points == 850

    def test_real_chat_history_pagination(self, real_db_setup):
        """Тест реальной пагинации истории чата"""
        from bot.models import ChatHistory, User

        session, _ = real_db_setup

        # Создаём пользователя
        user = User(telegram_id=100002, username="chat_user")
        session.add(user)
        session.commit()

        # Добавляем много сообщений
        for i in range(20):
            msg = ChatHistory(
                user_telegram_id=100002,
                message_text=f"Сообщение {i}",
                message_type="user" if i % 2 == 0 else "ai",
            )
            session.add(msg)

        session.commit()

        # Проверяем количество
        from sqlalchemy import select

        stmt = select(ChatHistory).where(ChatHistory.user_telegram_id == 100002)
        messages = session.execute(stmt).scalars().all()

        assert len(messages) == 20

    def test_real_learning_session_statistics(self, real_db_setup):
        """Тест реальной статистики обучающих сессий"""
        from bot.models import LearningSession, User

        session, _ = real_db_setup

        # Создаём пользователя
        user = User(telegram_id=100003, username="learning_user")
        session.add(user)
        session.commit()

        # Создаём несколько сессий
        for i in range(5):
            ls = LearningSession(
                user_telegram_id=100003,
                subject="физика",
                topic=f"Тема {i}",
                questions_answered=10,
                correct_answers=7 + i,
            )
            session.add(ls)

        session.commit()

        # Проверяем
        from sqlalchemy import select

        stmt = select(LearningSession).where(LearningSession.user_telegram_id == 100003)
        sessions = session.execute(stmt).scalars().all()

        assert len(sessions) == 5
        assert all(s.subject == "физика" for s in sessions)


class TestRealConfigurationAccess:
    """Реальные тесты доступа к конфигурации"""

    def test_real_config_database_url(self):
        """Тест реального доступа к DATABASE_URL"""
        from bot.config import settings

        assert settings.database_url is not None
        assert isinstance(settings.database_url, str)
        assert len(settings.database_url) > 0

    def test_real_config_telegram_token(self):
        """Тест реального доступа к Telegram токену"""
        from bot.config import settings

        assert settings.telegram_bot_token is not None
        assert isinstance(settings.telegram_bot_token, str)
        assert len(settings.telegram_bot_token) > 0

    def test_real_config_secret_key(self):
        """Тест реальной проверки секретного ключа"""
        from bot.config import settings

        assert settings.secret_key is not None
        assert len(settings.secret_key) >= 32

    def test_real_config_ai_settings(self):
        """Тест реальных настроек AI"""
        from bot.config import settings

        assert settings.ai_temperature > 0
        assert settings.ai_max_tokens > 0
        assert settings.ai_rate_limit_per_minute > 0

    def test_real_config_content_filter(self):
        """Тест реальных настроек фильтрации контента"""
        from bot.config import settings

        assert settings.content_filter_level >= 1
        assert settings.content_filter_level <= 5


class TestRealSecurityFeatures:
    """Реальные тесты функций безопасности"""

    def test_real_checksum_consistency(self):
        """Тест согласованности контрольных сумм"""
        from bot.security import IntegrityChecker

        data = "Test data for consistency check"

        # Вычисляем контрольную сумму дважды
        checksum1 = IntegrityChecker.calculate_checksum(data)
        checksum2 = IntegrityChecker.calculate_checksum(data)

        # Должны быть идентичными
        assert checksum1 == checksum2

    def test_real_checksum_different_data(self):
        """Тест различных контрольных сумм для разных данных"""
        from bot.security import IntegrityChecker

        data1 = "Data 1"
        data2 = "Data 2"

        checksum1 = IntegrityChecker.calculate_checksum(data1)
        checksum2 = IntegrityChecker.calculate_checksum(data2)

        # Должны быть разными
        assert checksum1 != checksum2

    def test_real_sanitize_multiple_inputs(self):
        """Тест реальной санитизации нескольких входных данных"""
        from bot.security import sanitize_input

        test_cases = [
            ("Normal text", "Normal text"),
            ("Text\x00with\x01nulls", "Textwith"),
            ("  spaced text  ", "  spaced text  "),
            ("Mixed\x00normal\x01and\x02bad", "Mixednormalandbad"),
        ]

        for input_data, expected_pattern in test_cases:
            result = sanitize_input(input_data)
            assert "\x00" not in result
            assert "\x01" not in result
            assert "\x02" not in result

    def test_real_url_safety_validation(self):
        """Тест реальной валидации URL безопасности"""
        from bot.security import validate_url_safety

        safe_urls = [
            "https://api.telegram.org/bot123/test",
        ]

        unsafe_urls = [
            "http://insecure.com",  # HTTP
            "https://192.168.1.1",  # IP
            "https://10.0.0.1",  # Private IP
            "https://127.0.0.1",  # Localhost
            "https://google.com/search",  # Не в белом списке
        ]

        for url in safe_urls:
            assert validate_url_safety(url) is True, f"{url} должен быть безопасным"

        for url in unsafe_urls:
            assert validate_url_safety(url) is False, f"{url} должен быть небезопасным"


class TestRealModerationWorkflows:
    """Реальные тесты процессов модерации"""

    def test_real_moderation_safe_educational_content(self):
        """Тест реальной модерации образовательного контента"""
        from bot.services.moderation_service import ContentModerationService

        service = ContentModerationService()

        educational_topics = [
            "Помоги решить задачу по алгебре",
            "Объясни теорему Пифагора",
            "Что такое квадратное уравнение?",
            "История Великой Отечественной войны",
            "Биология: строение клетки",
            "Физика: законы Ньютона",
            "Химия: таблица Менделеева",
            "География: континенты и океаны",
        ]

        for content in educational_topics:
            is_safe, reason = service.is_safe_content(content)
            assert is_safe is True, f"Образовательный контент должен быть безопасен: {content}"

    def test_real_moderation_blocked_categories(self):
        """Тест реальной модерации запрещённых категорий"""
        from bot.services.moderation_service import ContentModerationService

        service = ContentModerationService()

        # Проверяем разные категории запрещённого контента
        blocked_samples = {
            "profanity": ["блять", "хуй", "пизда"],
            "drugs": ["наркотики", "героин", "кокаин"],
            "violence": ["убить", "оружие"],
        }

        for category, samples in blocked_samples.items():
            for sample in samples:
                is_safe, reason = service.is_safe_content(sample)
                assert is_safe is False, (
                    f"Контент категории {category} должен быть заблокирован: {sample}"
                )
                assert reason is not None

    def test_real_moderation_mixed_content(self):
        """Тест реальной модерации смешанного контента"""
        from bot.services.moderation_service import ContentModerationService

        service = ContentModerationService()

        # Текст с запрещённым словом внутри нормального вопроса
        mixed = "Привет! Помоги с домашкой. А еще расскажи про героин в истории медицины."

        is_safe, reason = service.is_safe_content(mixed)
        # Должно быть заблокировано из-за слова "героин"
        assert is_safe is False


class TestRealModelRelationships:
    """Реальные тесты связей между моделями"""

    @pytest.fixture(scope="function")
    def real_db(self):
        """Реальная БД для тестов"""
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

    def test_real_parent_child_relationship(self, real_db):
        """Тест реальной связи родитель-ребёнок"""
        from bot.models import User

        # Создаём родителя
        parent = User(
            telegram_id=200001, username="parent_real", first_name="Parent", user_type="parent"
        )
        real_db.add(parent)
        real_db.commit()

        # Создаём ребёнка со ссылкой на родителя
        child = User(
            telegram_id=200002,
            username="child_real",
            first_name="Child",
            user_type="child",
            parent_telegram_id=200001,
        )
        real_db.add(child)
        real_db.commit()

        # Проверяем связь
        assert child.parent_telegram_id == parent.telegram_id

    def test_real_user_chat_history_relationship(self, real_db):
        """Тест реальной связи пользователь-история"""
        from bot.models import ChatHistory, User

        # Создаём пользователя
        user = User(telegram_id=200003, username="history_user")
        real_db.add(user)
        real_db.commit()

        # Добавляем историю
        for i in range(3):
            msg = ChatHistory(
                user_telegram_id=200003, message_text=f"Message {i}", message_type="user"
            )
            real_db.add(msg)

        real_db.commit()

        # Проверяем
        from sqlalchemy import select

        stmt = select(ChatHistory).where(ChatHistory.user_telegram_id == 200003)
        messages = real_db.execute(stmt).scalars().all()

        assert len(messages) == 3
        assert all(m.user_telegram_id == 200003 for m in messages)


class TestRealMonitoringFunctions:
    """Реальные тесты функций мониторинга"""

    def test_real_log_user_activity_no_error(self):
        """Тест что логирование активности не падает"""
        from bot.monitoring import log_user_activity

        # Не должно падать
        try:
            log_user_activity(12345, "test_action")
            assert True
        except Exception as e:
            pytest.fail(f"log_user_activity raised exception: {e}")

    def test_real_monitoring_with_various_data(self):
        """Тест мониторинга с различными данными"""
        from bot.monitoring import log_user_activity

        test_cases = [
            (12345, "message_sent"),
            (67890, "command_executed"),
            (11111, "ai_response"),
        ]

        for user_id, action in test_cases:
            try:
                log_user_activity(user_id, action)
                assert True
            except Exception as e:
                pytest.fail(f"Monitoring failed for {action}: {e}")
