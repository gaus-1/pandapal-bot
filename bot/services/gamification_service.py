"""
Сервис геймификации для PandaPal Bot.

Реализует систему достижений, очков опыта (XP) и уровней для мотивации
пользователей к активному обучению.

Основные возможности:
- Начисление XP за активность
- Разблокировка достижений
- Подсчет прогресса по различным метрикам
- Система уровней
"""

from datetime import UTC, datetime, timedelta

from loguru import logger
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from bot.models import ChatHistory, UserProgress


class Achievement:
    """Класс для определения достижения"""

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        icon: str,
        xp_reward: int,
        condition_type: str,
        condition_value: int,
    ):
        """
        Инициализация достижения.

        Args:
            id: Уникальный идентификатор достижения
            title: Название достижения
            description: Описание достижения
            icon: Эмодзи-иконка достижения
            xp_reward: Количество XP за получение достижения
            condition_type: Тип условия ('messages', 'questions', 'days', 'subjects', 'tasks')
            condition_value: Значение условия для разблокировки
        """
        self.id = id
        self.title = title
        self.description = description
        self.icon = icon
        self.xp_reward = xp_reward
        self.condition_type = condition_type  # 'messages', 'questions', 'days', 'subjects', 'tasks'
        self.condition_value = condition_value


# Определения всех достижений
ALL_ACHIEVEMENTS = [
    # Базовые достижения (доступны всем)
    Achievement("first_step", "Первый шаг", "Отправь первое сообщение", "🌟", 10, "messages", 1),
    Achievement("chatterbox", "Болтун", "Отправь 100 сообщений", "💬", 50, "messages", 100),
    Achievement("curious", "Любознательный", "Задай 50 вопросов", "❓", 100, "questions", 50),
    Achievement(
        "week_streak", "Неделя подряд", "Используй бота 7 дней подряд", "🔥", 200, "days", 7
    ),
    Achievement("excellent", "Отличник", "Реши 20 задач правильно", "🎓", 150, "tasks", 20),
    Achievement("erudite", "Эрудит", "Задавай вопросы по 5+ предметам", "📚", 300, "subjects", 5),
    Achievement("dedicated", "Преданный", "Отправь 500 сообщений", "💪", 400, "messages", 500),
    Achievement("scholar", "Ученый", "Задай 200 вопросов", "🎓", 500, "questions", 200),
    Achievement(
        "month_streak", "Месяц подряд", "Используй бота 30 дней подряд", "⭐", 1000, "days", 30
    ),
    # ЭКСКЛЮЗИВНЫЕ достижения для Premium (требуют premium статус)
    Achievement(
        "premium_master",
        "Premium Мастер",
        "Premium: 1000 AI запросов",
        "👑",
        1000,
        "premium_requests",
        1000,
    ),
    Achievement(
        "premium_expert",
        "Premium Эксперт",
        "Premium: все предметы изучены",
        "💎",
        1500,
        "premium_subjects",
        8,
    ),
    Achievement(
        "premium_champion",
        "Premium Чемпион",
        "Premium: 30 дней активности",
        "🏆",
        2000,
        "premium_days",
        30,
    ),
    Achievement(
        "vip_legend", "VIP Легенда", "VIP: годовая подписка активна", "🌟", 5000, "vip_status", 1
    ),
    # Игровые достижения
    Achievement("first_game_win", "Первая победа", "Победи панду в игре", "🎮", 50, "game_wins", 1),
    Achievement("game_master_10", "Мастер игр", "Победи панду 10 раз", "🏆", 200, "game_wins", 10),
    Achievement(
        "game_champion_50", "Чемпион игр", "Победи панду 50 раз", "👑", 500, "game_wins", 50
    ),
    Achievement("game_addict_100", "Игроман", "Сыграй 100 партий", "🎯", 300, "total_games", 100),
    Achievement(
        "tic_tac_toe_expert",
        "Эксперт крестиков",
        "10 побед в крестики-нолики",
        "⭕",
        150,
        "tic_tac_toe_wins",
        10,
    ),
    Achievement(
        "checkers_master", "Мастер шашек", "10 побед в шашки", "🎯", 150, "checkers_wins", 10
    ),
    Achievement(
        "2048_legend", "Легенда 2048", "Набери 2048 очков", "🔢", 200, "2048_best_score", 2048
    ),
]


class GamificationService:
    """Сервис геймификации для начисления XP и разблокировки достижений"""

    def __init__(self, db: Session):
        """
        Инициализация сервиса геймификации.

        Args:
            db (Session): Сессия SQLAlchemy для работы с базой данных.
        """
        self.db = db
        self.xp_per_message = 1  # XP за каждое сообщение
        self.xp_per_question = 2  # XP за вопрос (определяется по наличию "?")

    def get_or_create_progress(self, telegram_id: int) -> UserProgress:
        """
        Получить или создать запись прогресса пользователя.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            UserProgress: Запись прогресса пользователя
        """
        stmt = select(UserProgress).where(UserProgress.user_telegram_id == telegram_id)
        progress = self.db.scalar(stmt)

        if not progress:
            progress = UserProgress(
                user_telegram_id=telegram_id,
                subject="general",  # Дефолтный предмет для общего прогресса
                points=0,
                level=1,
                achievements={},
            )
            self.db.add(progress)
            self.db.flush()
            logger.info(f"✅ Создан прогресс для user={telegram_id}")

        return progress

    def add_xp(self, telegram_id: int, xp_amount: int, reason: str = "") -> int:
        """
        Добавить очки опыта пользователю.

        Args:
            telegram_id: Telegram ID пользователя
            xp_amount: Количество XP для добавления
            reason: Причина начисления (для логирования)

        Returns:
            int: Новый уровень пользователя (если изменился)
        """
        progress = self.get_or_create_progress(telegram_id)
        old_level = progress.level

        progress.points += xp_amount
        new_level = self._calculate_level(progress.points)

        if new_level > old_level:
            progress.level = new_level
            logger.info(
                f"🎉 User {telegram_id} достиг уровня {new_level}! "
                f"(было {old_level}, XP: {progress.points})"
            )

        self.db.flush()

        if reason:
            logger.debug(f"➕ +{xp_amount} XP для user={telegram_id} ({reason})")

        return new_level if new_level > old_level else 0

    def _calculate_level(self, total_xp: int) -> int:
        """
        Вычислить уровень на основе общего количества XP.

        Формула: level = floor(sqrt(total_xp / 100)) + 1
        Уровень 1: 0-99 XP
        Уровень 2: 100-399 XP
        Уровень 3: 400-899 XP
        И т.д.

        Args:
            total_xp: Общее количество XP

        Returns:
            int: Уровень пользователя
        """
        if total_xp < 100:
            return 1
        import math

        level = int(math.sqrt(total_xp / 100)) + 1
        return min(level, 50)  # Максимальный уровень 50

    def process_message(self, telegram_id: int, message_text: str) -> list[str]:
        """
        Обработать сообщение пользователя и начислить XP, проверить достижения.

        Args:
            telegram_id: Telegram ID пользователя
            message_text: Текст сообщения

        Returns:
            List[str]: Список ID разблокированных достижений
        """
        unlocked_achievements = []

        # Начисляем базовый XP за сообщение
        self.add_xp(telegram_id, self.xp_per_message, "сообщение")

        # Если это вопрос (содержит "?"), начисляем дополнительный XP
        if "?" in message_text:
            self.add_xp(telegram_id, self.xp_per_question, "вопрос")

        # Проверяем достижения (кроме игровых - они проверяются только при завершении игр)
        unlocked = self.check_and_unlock_achievements(telegram_id, skip_game_achievements=True)
        unlocked_achievements.extend(unlocked)

        return unlocked_achievements

    def check_and_unlock_achievements(
        self, telegram_id: int, skip_game_achievements: bool = False
    ) -> list[str]:
        """
        Проверить и разблокировать достижения пользователя.

        Args:
            telegram_id: Telegram ID пользователя
            skip_game_achievements: Если True, пропускает проверку игровых достижений
                                   (они проверяются только при завершении игр)

        Returns:
            List[str]: Список ID разблокированных достижений
        """
        # КРИТИЧЕСКИ ВАЖНО: Загружаем progress заново из БД, чтобы получить актуальные данные
        # Это предотвращает повторное разблокирование уже разблокированных достижений
        # НО: db.expire/refresh работают только в рамках одной транзакции!
        # Если данные уже закоммичены в предыдущей транзакции, нужно делать новый запрос
        # Решение: всегда делаем новый запрос из БД, чтобы гарантировать актуальность

        # Делаем flush всех изменений перед запросом, чтобы увидеть незакоммиченные изменения
        self.db.flush()

        # КРИТИЧЕСКИ ВАЖНО: Делаем НОВЫЙ запрос к БД, чтобы получить актуальные данные
        # Это гарантирует, что мы увидим уже разблокированные достижения из предыдущих транзакций
        progress = self.get_or_create_progress(telegram_id)

        # Принудительно сбрасываем кеш и перезагружаем achievements из БД
        self.db.expire(progress, ["achievements"])
        try:
            self.db.refresh(progress, attribute_names=["achievements"])
        except Exception as e:
            # Если refresh не сработал, делаем еще один запрос
            logger.debug(f"⚠️ Не удалось refresh progress: {e}, делаем еще один запрос")
            progress = self.db.scalar(
                select(UserProgress).where(UserProgress.user_telegram_id == telegram_id)
            )
            if not progress:
                progress = self.get_or_create_progress(telegram_id)

        unlocked_achievements = progress.achievements or {}
        newly_unlocked = []

        # Дополнительная проверка: логируем уже разблокированные достижения для отладки
        if unlocked_achievements:
            logger.debug(
                f"🔍 Уже разблокированные достижения для user={telegram_id}: "
                f"{list(unlocked_achievements.keys())}"
            )

        # Проверяем premium статус для эксклюзивных достижений
        from bot.services.premium_features_service import PremiumFeaturesService

        premium_service = PremiumFeaturesService(self.db)
        is_premium = premium_service.is_premium_active(telegram_id)

        # Получаем статистику пользователя
        stats = self.get_user_stats(telegram_id)

        # Добавляем premium статистику
        if is_premium:
            # Подсчитываем premium-специфичные метрики
            stats["premium_requests"] = stats.get(
                "total_messages", 0
            )  # Все сообщения как premium запросы
            stats["premium_subjects"] = stats.get("unique_subjects", 0)
            stats["premium_days"] = stats.get("consecutive_days", 0)
            stats["vip_status"] = 1 if is_premium else 0

        for achievement in ALL_ACHIEVEMENTS:
            # Пропускаем уже разблокированные
            if achievement.id in unlocked_achievements:
                logger.debug(f"✅ Достижение '{achievement.id}' уже разблокировано, пропускаем")
                continue

            # КРИТИЧЕСКИ ВАЖНО: Игровые достижения проверяются ТОЛЬКО при завершении игр,
            # а НЕ при обработке AI сообщений
            if skip_game_achievements:
                game_achievement_types = [
                    "game_wins",
                    "total_games",
                    "tic_tac_toe_wins",
                    "checkers_wins",
                    "2048_best_score",
                ]
                if achievement.condition_type in game_achievement_types:
                    logger.debug(
                        f"⏭️ Пропускаем игровое достижение '{achievement.id}' "
                        f"(проверяется только при завершении игр)"
                    )
                    continue  # Пропускаем игровые достижения при AI ответах

            # Проверяем premium требования для эксклюзивных достижений
            if (
                achievement.condition_type.startswith("premium_")
                or achievement.condition_type == "vip_status"
            ) and not is_premium:
                continue  # Пропускаем premium достижения для бесплатных

            # Проверяем VIP требования
            if achievement.id == "vip_legend" and not is_premium:
                continue  # VIP достижение только для Premium

            # Проверяем условие достижения
            if self._check_achievement_condition(achievement, stats):
                # Разблокируем достижение
                unlocked_achievements[achievement.id] = {
                    "unlocked_at": datetime.now(UTC).isoformat(),
                    "xp_reward": achievement.xp_reward,
                }

                # Начисляем XP за достижение
                self.add_xp(telegram_id, achievement.xp_reward, f"достижение: {achievement.title}")

                newly_unlocked.append(achievement.id)
                logger.info(
                    f"🏆 Достижение разблокировано: {achievement.title} "
                    f"(user={telegram_id}, +{achievement.xp_reward} XP)"
                )

        # Сохраняем обновленные достижения только если есть новые
        if newly_unlocked:
            progress.achievements = unlocked_achievements
            self.db.flush()  # flush для сохранения изменений в текущей транзакции
            # КРИТИЧЕСКИ ВАЖНО: коммит должен происходить в вызывающем коде, не здесь
            logger.debug(
                f"✅ Обновлены достижения для user={telegram_id}: "
                f"новых {len(newly_unlocked)}, всего {len(unlocked_achievements)}"
            )

        return newly_unlocked

    def _check_achievement_condition(self, achievement: Achievement, stats: dict) -> bool:
        """
        Проверить условие достижения.

        Args:
            achievement: Достижение для проверки
            stats: Статистика пользователя

        Returns:
            bool: True если условие выполнено
        """
        condition_type = achievement.condition_type
        condition_value = achievement.condition_value

        if condition_type == "messages":
            return stats.get("total_messages", 0) >= condition_value
        elif condition_type == "questions":
            return stats.get("total_questions", 0) >= condition_value
        elif condition_type == "days":
            return stats.get("consecutive_days", 0) >= condition_value
        elif condition_type == "subjects":
            return stats.get("unique_subjects", 0) >= condition_value
        elif condition_type == "tasks":
            return stats.get("solved_tasks", 0) >= condition_value
        elif condition_type == "premium_requests":
            return stats.get("premium_requests", 0) >= condition_value
        elif condition_type == "premium_subjects":
            return stats.get("premium_subjects", 0) >= condition_value
        elif condition_type == "premium_days":
            return stats.get("premium_days", 0) >= condition_value
        elif condition_type == "vip_status":
            return stats.get("vip_status", 0) >= condition_value
        elif condition_type == "game_wins":
            return stats.get("total_game_wins", 0) >= condition_value
        elif condition_type == "total_games":
            return stats.get("total_game_sessions", 0) >= condition_value
        elif condition_type == "tic_tac_toe_wins":
            return stats.get("tic_tac_toe_wins", 0) >= condition_value
        elif condition_type == "checkers_wins":
            return stats.get("checkers_wins", 0) >= condition_value
        elif condition_type == "2048_best_score":
            return stats.get("2048_best_score", 0) >= condition_value

        return False

    def get_user_stats(self, telegram_id: int) -> dict:
        """
        Получить статистику пользователя для проверки достижений.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Dict: Статистика пользователя
        """
        # Подсчет сообщений
        messages_stmt = select(func.count(ChatHistory.id)).where(
            and_(
                ChatHistory.user_telegram_id == telegram_id,
                ChatHistory.message_type == "user",
            )
        )
        total_messages = self.db.scalar(messages_stmt) or 0

        # Подсчет вопросов (сообщения с "?")
        questions_stmt = select(func.count(ChatHistory.id)).where(
            and_(
                ChatHistory.user_telegram_id == telegram_id,
                ChatHistory.message_type == "user",
                ChatHistory.message_text.like("%?%"),
            )
        )
        total_questions = self.db.scalar(questions_stmt) or 0

        # Подсчет дней подряд
        consecutive_days = self._calculate_consecutive_days(telegram_id)

        # Подсчет уникальных предметов (пока упрощенно - по ключевым словам)
        unique_subjects = self._count_unique_subjects(telegram_id)

        # Решенные задачи (пока 0, будет реализовано позже)
        solved_tasks = 0

        # Игровая статистика
        from bot.models import GameStats

        game_stats_stmt = select(GameStats).where(GameStats.user_telegram_id == telegram_id)
        game_stats_list = self.db.scalars(game_stats_stmt).all()

        total_game_wins = 0
        total_game_sessions = 0
        tic_tac_toe_wins = 0
        checkers_wins = 0
        game_2048_best_score = 0

        for gs in game_stats_list:
            total_game_wins += gs.wins
            total_game_sessions += gs.total_games
            if gs.game_type == "tic_tac_toe":
                tic_tac_toe_wins = gs.wins
            elif gs.game_type == "checkers":
                checkers_wins = gs.wins
            elif gs.game_type == "2048" and gs.best_score and gs.best_score > game_2048_best_score:
                game_2048_best_score = gs.best_score

        stats = {
            "total_messages": total_messages,
            "total_questions": total_questions,
            "consecutive_days": consecutive_days,
            "unique_subjects": unique_subjects,
            "solved_tasks": solved_tasks,
            "total_game_wins": total_game_wins,
            "total_game_sessions": total_game_sessions,
            "tic_tac_toe_wins": tic_tac_toe_wins,
            "checkers_wins": checkers_wins,
            "2048_best_score": game_2048_best_score,
        }
        # Premium-метрики для отображения прогресса по эксклюзивным достижениям
        from bot.services.premium_features_service import PremiumFeaturesService

        premium_service = PremiumFeaturesService(self.db)
        if premium_service.is_premium_active(telegram_id):
            stats["premium_requests"] = total_messages
            stats["premium_subjects"] = unique_subjects
            stats["premium_days"] = consecutive_days
            stats["vip_status"] = 1
        return stats

    def _calculate_consecutive_days(self, telegram_id: int) -> int:
        """
        Вычислить количество дней подряд активности.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            int: Количество дней подряд
        """
        # Получаем все даты сообщений пользователя
        stmt = (
            select(func.date(ChatHistory.timestamp))
            .where(ChatHistory.user_telegram_id == telegram_id)
            .distinct()
            .order_by(func.date(ChatHistory.timestamp).desc())
        )

        dates = [row[0] for row in self.db.execute(stmt).all()]

        if not dates:
            return 0

        # Подсчитываем дни подряд
        consecutive = 1
        today = datetime.now(UTC).date()

        # Если последнее сообщение не сегодня, начинаем с вчера
        if dates[0] != today:
            return 0

        for i in range(1, len(dates)):
            expected_date = today - timedelta(days=i)
            if dates[i] == expected_date:
                consecutive += 1
            else:
                break

        return consecutive

    def _count_unique_subjects(self, telegram_id: int) -> int:
        """
        Подсчитать количество уникальных предметов по ключевым словам.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            int: Количество уникальных предметов
        """
        from bot.config.subject_keywords import SUBJECT_KEYWORDS

        # Получаем все сообщения пользователя
        stmt = select(ChatHistory.message_text).where(
            and_(
                ChatHistory.user_telegram_id == telegram_id,
                ChatHistory.message_type == "user",
            )
        )

        messages = self.db.execute(stmt).scalars().all()
        found_subjects: set[str] = set()

        for message in messages:
            message_lower = message.lower()
            for subject, keywords in SUBJECT_KEYWORDS.items():
                if any(keyword in message_lower for keyword in keywords):
                    found_subjects.add(subject)
                    break

        return len(found_subjects)

    def get_achievements_with_progress(self, telegram_id: int) -> list[dict]:
        """
        Получить все достижения с прогрессом пользователя.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            List[Dict]: Список достижений с информацией о прогрессе
        """
        progress = self.get_or_create_progress(telegram_id)
        unlocked_achievements = progress.achievements or {}
        stats = self.get_user_stats(telegram_id)

        result = []

        for achievement in ALL_ACHIEVEMENTS:
            is_unlocked = achievement.id in unlocked_achievements
            progress_value = self._get_achievement_progress(achievement, stats)

            result.append(
                {
                    "id": achievement.id,
                    "title": achievement.title,
                    "description": achievement.description,
                    "icon": achievement.icon,
                    "xp_reward": achievement.xp_reward,
                    "unlocked": is_unlocked,
                    "unlock_date": (
                        unlocked_achievements.get(achievement.id, {}).get("unlocked_at")
                        if is_unlocked
                        else None
                    ),
                    "progress": progress_value,
                    "progress_max": achievement.condition_value,
                }
            )

        return result

    def _get_achievement_progress(self, achievement: Achievement, stats: dict) -> int:
        """
        Получить текущий прогресс по достижению.

        Args:
            achievement: Достижение
            stats: Статистика пользователя

        Returns:
            int: Текущее значение прогресса
        """
        condition_type = achievement.condition_type

        if condition_type == "messages":
            return min(stats.get("total_messages", 0), achievement.condition_value)
        elif condition_type == "questions":
            return min(stats.get("total_questions", 0), achievement.condition_value)
        elif condition_type == "days":
            return min(stats.get("consecutive_days", 0), achievement.condition_value)
        elif condition_type == "subjects":
            return min(stats.get("unique_subjects", 0), achievement.condition_value)
        elif condition_type == "tasks":
            return min(stats.get("solved_tasks", 0), achievement.condition_value)
        elif condition_type == "game_wins":
            return min(stats.get("total_game_wins", 0), achievement.condition_value)
        elif condition_type == "total_games":
            return min(stats.get("total_game_sessions", 0), achievement.condition_value)
        elif condition_type == "tic_tac_toe_wins":
            return min(stats.get("tic_tac_toe_wins", 0), achievement.condition_value)
        elif condition_type == "checkers_wins":
            return min(stats.get("checkers_wins", 0), achievement.condition_value)
        elif condition_type == "2048_best_score":
            return min(stats.get("2048_best_score", 0), achievement.condition_value)
        elif condition_type == "premium_requests":
            return min(stats.get("premium_requests", 0), achievement.condition_value)
        elif condition_type == "premium_subjects":
            return min(stats.get("premium_subjects", 0), achievement.condition_value)
        elif condition_type == "premium_days":
            return min(stats.get("premium_days", 0), achievement.condition_value)
        elif condition_type == "vip_status":
            return 1 if stats.get("vip_status", 0) >= achievement.condition_value else 0

        return 0

    def get_user_progress_summary(self, telegram_id: int) -> dict:
        """
        Получить сводку прогресса пользователя.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Dict: Сводка прогресса (уровень, XP, достижения)
        """
        progress = self.get_or_create_progress(telegram_id)
        stats = self.get_user_stats(telegram_id)
        unlocked_count = len(progress.achievements or {})

        # Вычисляем XP до следующего уровня
        next_level_xp = self._get_level_xp_requirement(progress.level + 1)
        xp_for_next_level = next_level_xp - progress.points

        return {
            "level": progress.level,
            "xp": progress.points,
            "xp_for_next_level": max(0, xp_for_next_level),
            "achievements_unlocked": unlocked_count,
            "achievements_total": len(ALL_ACHIEVEMENTS),
            "stats": stats,
        }

    def _get_level_xp_requirement(self, level: int) -> int:
        """
        Получить требуемое количество XP для уровня.

        Args:
            level: Уровень

        Returns:
            int: Требуемое количество XP
        """
        if level <= 1:
            return 0
        return int(((level - 1) ** 2) * 100)
