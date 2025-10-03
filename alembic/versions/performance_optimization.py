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
    
    # Индекс для поиска активных сессий
    op.create_index('ix_learning_sessions_active', 'learning_sessions', ['is_active'], if_not_exists=True)
    
    # Составной индекс для поиска сессий пользователя по дате
    op.create_index('ix_learning_sessions_user_date', 'learning_sessions', ['user_telegram_id', 'started_at'], if_not_exists=True)
    
    # ============ ИНДЕКСЫ ДЛЯ ТАБЛИЦЫ USER_PROGRESS ============
    
    # Индекс для поиска прогресса по пользователю
    op.create_index('ix_user_progress_user_telegram_id', 'user_progress', ['user_telegram_id'], if_not_exists=True)
    
    # Индекс для поиска по предмету
    op.create_index('ix_user_progress_subject', 'user_progress', ['subject'], if_not_exists=True)
    
    # Составной индекс для поиска прогресса пользователя по предмету
    op.create_index('ix_user_progress_user_subject', 'user_progress', ['user_telegram_id', 'subject'], if_not_exists=True)
    
    # ============ ЧАСТИЧНЫЕ ИНДЕКСЫ ДЛЯ ОПТИМИЗАЦИИ ============
    
    # Индекс только для активных пользователей
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_users_active_only 
        ON users (telegram_id) 
        WHERE is_active = true
    """)
    
    # Индекс только для детей с привязанными родителями
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_users_children_with_parents 
        ON users (parent_telegram_id, telegram_id) 
        WHERE user_type = 'child' AND parent_telegram_id IS NOT NULL
    """)
    
    # Индекс для недавних сообщений (последние 30 дней)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_chat_history_recent 
        ON chat_history (user_telegram_id, timestamp DESC) 
        WHERE timestamp > NOW() - INTERVAL '30 days'
    """)
    
    # ============ ОПТИМИЗАЦИЯ ТАБЛИЦ ============
    
    # Обновляем статистику таблиц для оптимизатора запросов
    op.execute("ANALYZE users")
    op.execute("ANALYZE chat_history")
    op.execute("ANALYZE learning_sessions")
    op.execute("ANALYZE user_progress")
    
    # ============ НАСТРОЙКИ POSTGRESQL ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ ============
    
    # Увеличиваем shared_buffers (если возможно)
    op.execute("""
        ALTER SYSTEM SET shared_buffers = '256MB' 
        WHERE name = 'shared_buffers' AND setting < '256MB'
    """)
    
    # Настраиваем effective_cache_size
    op.execute("""
        ALTER SYSTEM SET effective_cache_size = '1GB' 
        WHERE name = 'effective_cache_size' AND setting < '1GB'
    """)
    
    # Включаем логирование медленных запросов
    op.execute("""
        ALTER SYSTEM SET log_min_duration_statement = 1000
        WHERE name = 'log_min_duration_statement' AND setting = '0'
    """)
    
    # Настраиваем autovacuum для частых обновлений
    op.execute("""
        ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1
        WHERE name = 'autovacuum_vacuum_scale_factor' AND setting::float > 0.1
    """)
    
    # Перезагружаем конфигурацию
    op.execute("SELECT pg_reload_conf()")


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
    op.drop_index('ix_learning_sessions_active', 'learning_sessions', if_exists=True)
    op.drop_index('ix_learning_sessions_user_date', 'learning_sessions', if_exists=True)
    
    op.drop_index('ix_user_progress_user_telegram_id', 'user_progress', if_exists=True)
    op.drop_index('ix_user_progress_subject', 'user_progress', if_exists=True)
    op.drop_index('ix_user_progress_user_subject', 'user_progress', if_exists=True)
    
    # Удаляем частичные индексы
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_users_active_only")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_users_children_with_parents")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_chat_history_recent")
    
    # Возвращаем настройки PostgreSQL к значениям по умолчанию
    op.execute("ALTER SYSTEM RESET shared_buffers")
    op.execute("ALTER SYSTEM RESET effective_cache_size")
    op.execute("ALTER SYSTEM RESET log_min_duration_statement")
    op.execute("ALTER SYSTEM RESET autovacuum_vacuum_scale_factor")
    
    # Перезагружаем конфигурацию
    op.execute("SELECT pg_reload_conf()")
