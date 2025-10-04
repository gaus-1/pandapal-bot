"""
Миграция для оптимизации производительности базы данных
Добавляет индексы и оптимизирует структуру таблиц
@module alembic.versions.performance_optimization
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'performance_opt'
down_revision = '0fb5d4bc5f51'  # Предыдущая миграция
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Оптимизация производительности базы данных"""
    
    # ============ ИНДЕКСЫ ДЛЯ ТАБЛИЦЫ USERS ============
    
    # Индекс для поиска пользователей по telegram_id (уже есть, но убеждаемся)
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True, if_not_exists=True)
    
    # Индекс для поиска детей по родителю
    op.create_index('ix_users_parent_telegram_id', 'users', ['parent_telegram_id'], if_not_exists=True)
    
    # Индекс для поиска по типу пользователя
    op.create_index('ix_users_user_type', 'users', ['user_type'], if_not_exists=True)
    
    # Составной индекс для поиска активных пользователей определенного типа
    op.create_index('ix_users_type_active', 'users', ['user_type', 'is_active'], if_not_exists=True)
    
    # Индекс для поиска по возрасту и классу (для детей)
    op.create_index('ix_users_age_grade', 'users', ['age', 'grade'], if_not_exists=True)
    
    # ============ ИНДЕКСЫ ДЛЯ ТАБЛИЦЫ CHAT_HISTORY ============
    
    # Индекс для поиска истории по пользователю
    op.create_index('ix_chat_history_user_telegram_id', 'chat_history', ['user_telegram_id'], if_not_exists=True)
    
    # Индекс для поиска по типу сообщения
    op.create_index('ix_chat_history_message_type', 'chat_history', ['message_type'], if_not_exists=True)
    
    # Составной индекс для поиска последних сообщений пользователя
    op.create_index('ix_chat_history_user_timestamp', 'chat_history', ['user_telegram_id', 'timestamp'], if_not_exists=True)
    
    # Индекс для очистки старых сообщений
    op.create_index('ix_chat_history_timestamp', 'chat_history', ['timestamp'], if_not_exists=True)
    
    # ============ ИНДЕКСЫ ДЛЯ ТАБЛИЦЫ LEARNING_SESSIONS ============
    
    # Индекс для поиска сессий по пользователю
    op.create_index('ix_learning_sessions_user_telegram_id', 'learning_sessions', ['user_telegram_id'], if_not_exists=True)
    
    # Индекс для поиска завершенных сессий
    op.create_index('ix_learning_sessions_completed', 'learning_sessions', ['is_completed'], if_not_exists=True)
    
    # Составной индекс для поиска сессий пользователя по дате
    op.create_index('ix_learning_sessions_user_date', 'learning_sessions', ['user_telegram_id', 'session_start'], if_not_exists=True)
    
    # ============ ИНДЕКСЫ ДЛЯ ТАБЛИЦЫ USER_PROGRESS ============
    
    # Индекс для поиска прогресса по пользователю
    op.create_index('ix_user_progress_user_telegram_id', 'user_progress', ['user_telegram_id'], if_not_exists=True)
    
    # Индекс для поиска по предмету
    op.create_index('ix_user_progress_subject', 'user_progress', ['subject'], if_not_exists=True)
    
    # Составной индекс для поиска прогресса пользователя по предмету
    op.create_index('ix_user_progress_user_subject', 'user_progress', ['user_telegram_id', 'subject'], if_not_exists=True)
    
    # ============ ДОПОЛНИТЕЛЬНЫЕ ИНДЕКСЫ ДЛЯ ОПТИМИЗАЦИИ ============
    
    # Индекс для активных пользователей
    op.create_index('ix_users_active', 'users', ['is_active'], if_not_exists=True)
    
    # Индекс для типа пользователя
    op.create_index('ix_users_user_type', 'users', ['user_type'], if_not_exists=True)
    
    # ============ ОПТИМИЗАЦИЯ ТАБЛИЦ ============
    
    # Обновляем статистику таблиц для оптимизатора запросов
    op.execute("ANALYZE users")
    op.execute("ANALYZE chat_history")
    op.execute("ANALYZE learning_sessions")
    op.execute("ANALYZE user_progress")
    
    # ============ ФИНАЛЬНАЯ ОПТИМИЗАЦИЯ ============
    
    # Обновляем статистику для всех таблиц
    op.execute("ANALYZE")


def downgrade() -> None:
    """Откат оптимизаций производительности"""
    
    # Удаляем индексы
    op.drop_index('ix_users_telegram_id', 'users', if_exists=True)
    op.drop_index('ix_users_parent_telegram_id', 'users', if_exists=True)
    op.drop_index('ix_users_user_type', 'users', if_exists=True)
    op.drop_index('ix_users_type_active', 'users', if_exists=True)
    op.drop_index('ix_users_age_grade', 'users', if_exists=True)
    
    op.drop_index('ix_chat_history_user_telegram_id', 'chat_history', if_exists=True)
    op.drop_index('ix_chat_history_message_type', 'chat_history', if_exists=True)
    op.drop_index('ix_chat_history_user_timestamp', 'chat_history', if_exists=True)
    op.drop_index('ix_chat_history_timestamp', 'chat_history', if_exists=True)
    
    op.drop_index('ix_learning_sessions_user_telegram_id', 'learning_sessions', if_exists=True)
    op.drop_index('ix_learning_sessions_completed', 'learning_sessions', if_exists=True)
    op.drop_index('ix_learning_sessions_user_date', 'learning_sessions', if_exists=True)
    
    op.drop_index('ix_user_progress_user_telegram_id', 'user_progress', if_exists=True)
    op.drop_index('ix_user_progress_subject', 'user_progress', if_exists=True)
    op.drop_index('ix_user_progress_user_subject', 'user_progress', if_exists=True)
    
    # Удаляем дополнительные индексы
    op.drop_index('ix_users_active', 'users', if_exists=True)
    op.drop_index('ix_users_user_type', 'users', if_exists=True)
    
    # Финальная очистка
    op.execute("ANALYZE")
