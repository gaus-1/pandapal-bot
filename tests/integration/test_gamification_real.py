"""
РЕАЛЬНЫЕ интеграционные тесты для системы геймификации
БЕЗ МОКОВ - только реальные операции с БД

Тестируем:
- Начисление XP за сообщения
- Разблокировку достижений
- Подсчет прогресса (сообщения, вопросы, дни, предметы)
- Систему уровней
- Все достижения
"""

import os
import tempfile
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, ChatHistory, User
from bot.services.gamification_service import (
    ALL_ACHIEVEMENTS,
    GamificationService,
)


class TestGamificationReal:
    """Реальные тесты системы геймификации"""

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

    @pytest.fixture
    def test_user(self, real_db_session):
        """Создаёт тестового пользователя в БД"""
        user = User(
            telegram_id=999888777,
            username="test_gamification_user",
            first_name="Тестовый",
            last_name="Геймификация",
            user_type="child",
            age=10,
            grade=5,
        )
        real_db_session.add(user)
        real_db_session.commit()
        return user

    @pytest.fixture
    def gamification_service(self, real_db_session):
        """Создаёт сервис геймификации"""
        return GamificationService(real_db_session)

    def test_xp_earned_for_message(self, real_db_session, test_user, gamification_service):
        """Тест: XP начисляется за сообщение"""
        initial_progress = gamification_service.get_or_create_progress(test_user.telegram_id)
        initial_xp = initial_progress.points

        # Отправляем сообщение
        unlocked = gamification_service.process_message(
            test_user.telegram_id, "Привет! Помоги с математикой"
        )

        real_db_session.commit()
        real_db_session.refresh(initial_progress)

        # Проверяем что XP увеличился
        assert initial_progress.points > initial_xp, "XP не начислен за сообщение"
        assert initial_progress.points == initial_xp + 1, "XP должен быть +1 за сообщение"

    def test_xp_earned_for_question(self, real_db_session, test_user, gamification_service):
        """Тест: Дополнительный XP за вопрос (сообщение с '?')"""
        initial_progress = gamification_service.get_or_create_progress(test_user.telegram_id)
        initial_xp = initial_progress.points

        # Отправляем вопрос
        unlocked = gamification_service.process_message(
            test_user.telegram_id, "Что такое математика?"
        )

        real_db_session.commit()
        real_db_session.refresh(initial_progress)

        # Проверяем что XP увеличился на 3 (1 за сообщение + 2 за вопрос)
        assert initial_progress.points >= initial_xp + 3, "XP должен быть +3 за вопрос"

    def test_first_achievement_unlocked(self, real_db_session, test_user, gamification_service):
        """Тест: Разблокировка достижения 'Первый шаг' после первого сообщения"""
        # Отправляем первое сообщение
        unlocked = gamification_service.process_message(test_user.telegram_id, "Привет!")

        real_db_session.commit()

        # Проверяем что достижение разблокировано
        assert "first_step" in unlocked, "Достижение 'Первый шаг' должно быть разблокировано"

        # Проверяем в БД
        progress = gamification_service.get_or_create_progress(test_user.telegram_id)
        assert "first_step" in (progress.achievements or {}), "Достижение должно быть в БД"

    def test_chatterbox_achievement_progress(
        self, real_db_session, test_user, gamification_service
    ):
        """Тест: Прогресс по достижению 'Болтун' (100 сообщений)"""
        # Отправляем 50 сообщений
        for i in range(50):
            message = ChatHistory(
                user_telegram_id=test_user.telegram_id,
                message_text=f"Сообщение {i}",
                message_type="user",
            )
            real_db_session.add(message)
        real_db_session.commit()

        # Проверяем прогресс
        achievements = gamification_service.get_achievements_with_progress(test_user.telegram_id)
        chatterbox = next(a for a in achievements if a["id"] == "chatterbox")

        assert chatterbox["progress"] == 50, "Прогресс должен быть 50/100"
        assert not chatterbox["unlocked"], "Достижение не должно быть разблокировано"

    def test_chatterbox_achievement_unlocked(
        self, real_db_session, test_user, gamification_service
    ):
        """Тест: Разблокировка достижения 'Болтун' после 100 сообщений"""
        # Отправляем 100 сообщений
        for i in range(100):
            unlocked = gamification_service.process_message(test_user.telegram_id, f"Сообщение {i}")
            real_db_session.commit()

        # Проверяем что достижение разблокировано
        achievements = gamification_service.get_achievements_with_progress(test_user.telegram_id)
        chatterbox = next(a for a in achievements if a["id"] == "chatterbox")

        assert chatterbox["unlocked"], "Достижение 'Болтун' должно быть разблокировано"
        assert chatterbox["progress"] == 100, "Прогресс должен быть 100/100"

    def test_curious_achievement_progress(self, real_db_session, test_user, gamification_service):
        """Тест: Прогресс по достижению 'Любознательный' (50 вопросов)"""
        # Отправляем 25 вопросов
        for i in range(25):
            message = ChatHistory(
                user_telegram_id=test_user.telegram_id,
                message_text=f"Вопрос {i}?",
                message_type="user",
            )
            real_db_session.add(message)
        real_db_session.commit()

        # Проверяем прогресс
        achievements = gamification_service.get_achievements_with_progress(test_user.telegram_id)
        curious = next(a for a in achievements if a["id"] == "curious")

        assert curious["progress"] == 25, "Прогресс должен быть 25/50"
        assert not curious["unlocked"], "Достижение не должно быть разблокировано"

    def test_level_calculation(self, real_db_session, test_user, gamification_service):
        """Тест: Правильный расчет уровня на основе XP"""
        progress = gamification_service.get_or_create_progress(test_user.telegram_id)

        # Уровень 1: 0-99 XP
        assert progress.level == 1, "Начальный уровень должен быть 1"

        # Добавляем 100 XP (должен быть уровень 2)
        gamification_service.add_xp(test_user.telegram_id, 100, "тест")
        real_db_session.commit()
        real_db_session.refresh(progress)

        assert progress.level >= 2, "Уровень должен быть >= 2 после 100 XP"

    def test_consecutive_days_calculation(self, real_db_session, test_user, gamification_service):
        """Тест: Подсчет дней подряд активности"""
        # Создаем сообщения за последние 3 дня
        today = datetime.utcnow()
        for day_offset in range(3):
            message_date = today - timedelta(days=day_offset)
            message = ChatHistory(
                user_telegram_id=test_user.telegram_id,
                message_text=f"Сообщение день {day_offset}",
                message_type="user",
                timestamp=message_date,
            )
            real_db_session.add(message)
        real_db_session.commit()

        # Проверяем подсчет дней
        stats = gamification_service.get_user_stats(test_user.telegram_id)
        assert stats["consecutive_days"] >= 1, "Должен быть хотя бы 1 день активности"

    def test_unique_subjects_count(self, real_db_session, test_user, gamification_service):
        """Тест: Подсчет уникальных предметов"""
        # Создаем сообщения с упоминанием разных предметов
        subjects_messages = [
            "Помоги с математикой",
            "Вопрос по русскому языку",
            "Задача по физике",
            "Вопрос по биологии",
            "Помоги с историей",
        ]

        for msg in subjects_messages:
            message = ChatHistory(
                user_telegram_id=test_user.telegram_id,
                message_text=msg,
                message_type="user",
            )
            real_db_session.add(message)
        real_db_session.commit()

        # Проверяем подсчет предметов
        stats = gamification_service.get_user_stats(test_user.telegram_id)
        assert stats["unique_subjects"] >= 3, "Должно быть минимум 3 предмета"

    def test_erudite_achievement_unlocked(self, real_db_session, test_user, gamification_service):
        """Тест: Разблокировка достижения 'Эрудит' (5+ предметов)"""
        # Создаем сообщения с упоминанием 5 разных предметов
        subjects_messages = [
            "Помоги с математикой",
            "Вопрос по русскому языку",
            "Задача по физике",
            "Вопрос по биологии",
            "Помоги с историей",
        ]

        for msg in subjects_messages:
            unlocked = gamification_service.process_message(test_user.telegram_id, msg)
            real_db_session.commit()

        # Проверяем что достижение разблокировано
        achievements = gamification_service.get_achievements_with_progress(test_user.telegram_id)
        erudite = next(a for a in achievements if a["id"] == "erudite")

        assert erudite["unlocked"], "Достижение 'Эрудит' должно быть разблокировано"
        assert erudite["progress"] >= 5, "Прогресс должен быть >= 5"

    def test_achievement_xp_reward(self, real_db_session, test_user, gamification_service):
        """Тест: XP начисляется при разблокировке достижения"""
        initial_progress = gamification_service.get_or_create_progress(test_user.telegram_id)
        initial_xp = initial_progress.points

        # Разблокируем достижение
        unlocked = gamification_service.process_message(test_user.telegram_id, "Привет!")
        real_db_session.commit()
        real_db_session.refresh(initial_progress)

        # Проверяем что XP увеличился (базовый + за достижение)
        first_step = next(a for a in ALL_ACHIEVEMENTS if a.id == "first_step")
        expected_xp = initial_xp + 1 + first_step.xp_reward  # 1 за сообщение + 10 за достижение

        assert initial_progress.points >= expected_xp, "XP должен включать награду за достижение"

    def test_all_achievements_defined(self):
        """Тест: Все достижения определены корректно"""
        assert len(ALL_ACHIEVEMENTS) > 0, "Должны быть определены достижения"

        # Проверяем что у всех достижений есть обязательные поля
        for achievement in ALL_ACHIEVEMENTS:
            assert achievement.id, "Достижение должно иметь ID"
            assert achievement.title, "Достижение должно иметь название"
            assert achievement.description, "Достижение должно иметь описание"
            assert achievement.icon, "Достижение должно иметь иконку"
            assert achievement.xp_reward > 0, "Достижение должно давать XP"
            assert achievement.condition_type, "Достижение должно иметь тип условия"
            assert achievement.condition_value > 0, "Достижение должно иметь значение условия"

    def test_progress_summary(self, real_db_session, test_user, gamification_service):
        """Тест: Получение сводки прогресса"""
        # Отправляем несколько сообщений
        for i in range(5):
            gamification_service.process_message(test_user.telegram_id, f"Сообщение {i}")
            real_db_session.commit()

        # Получаем сводку
        summary = gamification_service.get_user_progress_summary(test_user.telegram_id)

        assert "level" in summary, "Сводка должна содержать уровень"
        assert "xp" in summary, "Сводка должна содержать XP"
        assert "achievements_unlocked" in summary, "Сводка должна содержать количество достижений"
        assert summary["level"] >= 1, "Уровень должен быть >= 1"
        assert summary["xp"] >= 0, "XP должен быть >= 0"

    def test_multiple_achievements_unlocked(self, real_db_session, test_user, gamification_service):
        """Тест: Разблокировка нескольких достижений одновременно"""
        # Отправляем первое сообщение (разблокирует 'Первый шаг')
        unlocked1 = gamification_service.process_message(test_user.telegram_id, "Привет!")
        real_db_session.commit()

        assert "first_step" in unlocked1, "Первое достижение должно быть разблокировано"

        # Отправляем еще 99 сообщений (разблокирует 'Болтун')
        for i in range(99):
            unlocked = gamification_service.process_message(test_user.telegram_id, f"Сообщение {i}")
            real_db_session.commit()

        # Проверяем что оба достижения разблокированы
        achievements = gamification_service.get_achievements_with_progress(test_user.telegram_id)
        first_step = next(a for a in achievements if a["id"] == "first_step")
        chatterbox = next(a for a in achievements if a["id"] == "chatterbox")

        assert first_step["unlocked"], "Достижение 'Первый шаг' должно быть разблокировано"
        assert chatterbox["unlocked"], "Достижение 'Болтун' должно быть разблокировано"
