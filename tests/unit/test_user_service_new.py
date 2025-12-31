"""
Тесты для User Service
Проверка управления пользователями
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from bot.models import User
from bot.services.user_service import UserService


class TestUserService:
    """Тесты для сервиса пользователей"""

    @pytest.fixture
    def service(self):
        """Создание экземпляра сервиса"""
        return UserService()

    @pytest.fixture
    def mock_session(self):
        """Мок сессии базы данных"""
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.query = Mock()
        return session

    @pytest.fixture
    def mock_user(self):
        """Мок пользователя"""
        return User(
            telegram_id=12345,
            username="test_user",
            age=10,
            grade=5,
            user_type="child",
            created_at=datetime.now(),
        )

    @pytest.mark.unit
    def test_service_init(self, service):
        """Тест инициализации сервиса"""
        assert service is not None

    @pytest.mark.unit
    def test_create_user(self, service, mock_session):
        """Тест создания нового пользователя"""
        with patch("bot.services.user_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = service.create_user(
                telegram_id=12345,
                username="new_user",
                age=12,
                grade=6,
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.unit
    def test_get_user_exists(self, service, mock_session, mock_user):
        """Тест получения существующего пользователя"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_session.query.return_value = mock_query

        with patch("bot.services.user_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            user = service.get_user(telegram_id=12345)

            assert user is not None
            assert user.telegram_id == 12345
            assert user.username == "test_user"

    @pytest.mark.unit
    def test_get_user_not_exists(self, service, mock_session):
        """Тест получения несуществующего пользователя"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        with patch("bot.services.user_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            user = service.get_user(telegram_id=99999)

            assert user is None

    @pytest.mark.unit
    def test_update_user(self, service, mock_session, mock_user):
        """Тест обновления данных пользователя"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_session.query.return_value = mock_query

        with patch("bot.services.user_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            service.update_user(telegram_id=12345, age=11, grade=6)

            mock_session.commit.assert_called_once()

    @pytest.mark.unit
    def test_delete_user(self, service, mock_session, mock_user):
        """Тест удаления пользователя"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_session.query.return_value = mock_query
        mock_session.delete = Mock()

        with patch("bot.services.user_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            service.delete_user(telegram_id=12345)

            mock_session.delete.assert_called_once_with(mock_user)
            mock_session.commit.assert_called_once()

    @pytest.mark.unit
    def test_get_user_count(self, service, mock_session):
        """Тест подсчета пользователей"""
        mock_query = Mock()
        mock_query.count.return_value = 150
        mock_session.query.return_value = mock_query

        with patch("bot.services.user_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            count = service.get_user_count()

            assert count == 150

    @pytest.mark.unit
    def test_get_users_by_type(self, service, mock_session, mock_user):
        """Тест получения пользователей по типу"""
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_user]
        mock_session.query.return_value = mock_query

        with patch("bot.services.user_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            users = service.get_users_by_type(user_type="child")

            assert len(users) == 1
            assert users[0].user_type == "child"

    @pytest.mark.unit
    def test_update_last_activity(self, service, mock_session, mock_user):
        """Тест обновления времени последней активности"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_session.query.return_value = mock_query

        with patch("bot.services.user_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            service.update_last_activity(telegram_id=12345)

            mock_session.commit.assert_called_once()

    @pytest.mark.unit
    def test_is_user_exists(self, service, mock_session, mock_user):
        """Тест проверки существования пользователя"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_session.query.return_value = mock_query

        with patch("bot.services.user_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            exists = service.is_user_exists(telegram_id=12345)

            assert exists is True

    @pytest.mark.unit
    def test_get_or_create_user_existing(self, service, mock_session, mock_user):
        """Тест получения существующего или создания нового"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_session.query.return_value = mock_query

        with patch("bot.services.user_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            user = service.get_or_create_user(telegram_id=12345, username="test_user")

            assert user is not None
            # Новый пользователь не должен быть создан
            mock_session.add.assert_not_called()
