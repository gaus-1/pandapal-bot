"""
Миграция для создания моделей аналитики
Добавляет таблицы для хранения аналитических данных
@module alembic.versions.analytics_models
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json

# revision identifiers, used by Alembic.
revision = 'analytics_models'
down_revision = 'performance_opt'  # Предыдущая миграция
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создание таблиц для аналитики"""
    
    # Проверяем существование таблиц перед созданием
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Если все таблицы уже существуют - пропускаем миграцию
    required_tables = [
        'analytics_metrics', 'user_sessions', 'user_events',
        'analytics_reports', 'analytics_trends', 'analytics_alerts', 'analytics_config'
    ]
    if all(table in existing_tables for table in required_tables):
        print("✅ Все таблицы аналитики уже существуют, пропускаем миграцию")
        return
    
    # ============ ТАБЛИЦА АНАЛИТИЧЕСКИХ МЕТРИК ============
    if 'analytics_metrics' not in existing_tables:
        op.create_table('analytics_metrics',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('metric_name', sa.String(100), nullable=False, comment='Название метрики'),
            sa.Column('metric_value', sa.Float(), nullable=False, comment='Значение метрики'),
            sa.Column('metric_type', sa.String(50), nullable=False, comment='Тип метрики (counter, gauge, histogram)'),
            sa.Column('tags', sa.JSON(), nullable=True, comment='Теги для группировки метрик'),
            sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время записи'),
            sa.Column('period', sa.String(20), nullable=False, comment='Период агрегации (hour, day, week, month)'),
            sa.Column('user_telegram_id', sa.BigInteger(), nullable=True, comment='ID пользователя (если метрика пользовательская)'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Индексы для таблицы метрик
        op.create_index('ix_analytics_metrics_name_time', 'analytics_metrics', ['metric_name', 'timestamp'])
        op.create_index('ix_analytics_metrics_user_time', 'analytics_metrics', ['user_telegram_id', 'timestamp'])
        op.create_index('ix_analytics_metrics_period', 'analytics_metrics', ['period'])
    
    # ============ ТАБЛИЦА ПОЛЬЗОВАТЕЛЬСКИХ СЕССИЙ ============
    op.create_table('user_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_telegram_id', sa.BigInteger(), nullable=False, comment='ID пользователя'),
        sa.Column('session_start', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Начало сессии'),
        sa.Column('session_end', sa.DateTime(timezone=True), nullable=True, comment='Конец сессии'),
        sa.Column('session_duration', sa.Integer(), nullable=True, comment='Длительность сессии в секундах'),
        sa.Column('messages_count', sa.Integer(), default=0, comment='Количество сообщений в сессии'),
        sa.Column('ai_interactions', sa.Integer(), default=0, comment='Количество AI взаимодействий'),
        sa.Column('voice_messages', sa.Integer(), default=0, comment='Количество голосовых сообщений'),
        sa.Column('blocked_messages', sa.Integer(), default=0, comment='Количество заблокированных сообщений'),
        sa.Column('subjects_covered', sa.JSON(), nullable=True, comment='Предметы, изученные в сессии'),
        sa.Column('engagement_score', sa.Float(), nullable=True, comment='Индекс вовлеченности'),
        sa.Column('safety_score', sa.Float(), nullable=True, comment='Индекс безопасности'),
        sa.Column('session_type', sa.String(50), default='regular', comment='Тип сессии (learning, casual, support)'),
        sa.Column('device_info', sa.JSON(), nullable=True, comment='Информация об устройстве'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для таблицы сессий
    op.create_index('ix_user_sessions_user_start', 'user_sessions', ['user_telegram_id', 'session_start'])
    op.create_index('ix_user_sessions_duration', 'user_sessions', ['session_duration'])
    op.create_index('ix_user_sessions_type', 'user_sessions', ['session_type'])
    
    # ============ ТАБЛИЦА СОБЫТИЙ ПОЛЬЗОВАТЕЛЕЙ ============
    op.create_table('user_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_telegram_id', sa.BigInteger(), nullable=False, comment='ID пользователя'),
        sa.Column('event_type', sa.String(100), nullable=False, comment='Тип события'),
        sa.Column('event_data', sa.JSON(), nullable=True, comment='Данные события'),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время события'),
        sa.Column('session_id', sa.Integer(), nullable=True, comment='ID сессии'),
        sa.Column('importance', sa.String(20), default='normal', comment='Важность события (low, normal, high, critical)'),
        sa.Column('processed', sa.Boolean(), default=False, comment='Обработано ли событие'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для таблицы событий
    op.create_index('ix_user_events_user_time', 'user_events', ['user_telegram_id', 'timestamp'])
    op.create_index('ix_user_events_type', 'user_events', ['event_type'])
    op.create_index('ix_user_events_importance', 'user_events', ['importance'])
    op.create_index('ix_user_events_processed', 'user_events', ['processed'])
    
    # ============ ТАБЛИЦА АНАЛИТИЧЕСКИХ ОТЧЕТОВ ============
    op.create_table('analytics_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False, comment='Тип отчета'),
        sa.Column('report_period', sa.String(20), nullable=False, comment='Период отчета'),
        sa.Column('report_data', sa.JSON(), nullable=False, comment='Данные отчета'),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время генерации'),
        sa.Column('generated_by', sa.String(100), nullable=True, comment='Кто сгенерировал отчет'),
        sa.Column('parent_telegram_id', sa.BigInteger(), nullable=True, comment='ID родителя (если отчет для родителя)'),
        sa.Column('child_telegram_id', sa.BigInteger(), nullable=True, comment='ID ребенка (если отчет для ребенка)'),
        sa.Column('is_scheduled', sa.Boolean(), default=False, comment='Автоматически сгенерированный отчет'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для таблицы отчетов
    op.create_index('ix_analytics_reports_type_period', 'analytics_reports', ['report_type', 'report_period'])
    op.create_index('ix_analytics_reports_parent', 'analytics_reports', ['parent_telegram_id'])
    op.create_index('ix_analytics_reports_generated', 'analytics_reports', ['generated_at'])
    
    # ============ ТАБЛИЦА ТРЕНДОВ И ПРОГНОЗОВ ============
    op.create_table('analytics_trends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False, comment='Название метрики'),
        sa.Column('trend_direction', sa.String(20), nullable=False, comment='Направление тренда (up, down, stable)'),
        sa.Column('trend_strength', sa.Float(), nullable=False, comment='Сила тренда (0-1)'),
        sa.Column('confidence', sa.Float(), nullable=False, comment='Уверенность в тренде (0-1)'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False, comment='Начало периода'),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False, comment='Конец периода'),
        sa.Column('prediction_data', sa.JSON(), nullable=True, comment='Данные прогноза'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время создания'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для таблицы трендов
    op.create_index('ix_analytics_trends_metric', 'analytics_trends', ['metric_name'])
    op.create_index('ix_analytics_trends_period', 'analytics_trends', ['period_start', 'period_end'])
    op.create_index('ix_analytics_trends_confidence', 'analytics_trends', ['confidence'])
    
    # ============ ТАБЛИЦА АЛЕРТОВ И УВЕДОМЛЕНИЙ ============
    op.create_table('analytics_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False, comment='Тип алерта'),
        sa.Column('alert_level', sa.String(20), nullable=False, comment='Уровень алерта (info, warning, critical)'),
        sa.Column('alert_message', sa.Text(), nullable=False, comment='Сообщение алерта'),
        sa.Column('alert_data', sa.JSON(), nullable=True, comment='Данные алерта'),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время срабатывания'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True, comment='Время разрешения'),
        sa.Column('resolved_by', sa.String(100), nullable=True, comment='Кто разрешил алерт'),
        sa.Column('parent_telegram_id', sa.BigInteger(), nullable=True, comment='ID родителя для уведомления'),
        sa.Column('child_telegram_id', sa.BigInteger(), nullable=True, comment='ID ребенка (если алерт связан с ребенком)'),
        sa.Column('is_sent', sa.Boolean(), default=False, comment='Отправлено ли уведомление'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для таблицы алертов
    op.create_index('ix_analytics_alerts_type_level', 'analytics_alerts', ['alert_type', 'alert_level'])
    op.create_index('ix_analytics_alerts_parent', 'analytics_alerts', ['parent_telegram_id'])
    op.create_index('ix_analytics_alerts_triggered', 'analytics_alerts', ['triggered_at'])
    op.create_index('ix_analytics_alerts_resolved', 'analytics_alerts', ['resolved_at'])
    
    # ============ ТАБЛИЦА КОНФИГУРАЦИИ АНАЛИТИКИ ============
    op.create_table('analytics_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_key', sa.String(100), nullable=False, comment='Ключ конфигурации'),
        sa.Column('config_value', sa.JSON(), nullable=False, comment='Значение конфигурации'),
        sa.Column('config_type', sa.String(50), nullable=False, comment='Тип конфигурации'),
        sa.Column('description', sa.Text(), nullable=True, comment='Описание конфигурации'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время создания'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False, comment='Время обновления'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('config_key')
    )
    
    # Индекс для таблицы конфигурации
    op.create_index('ix_analytics_config_key', 'analytics_config', ['config_key'])
    
    # ============ ВСТАВКА БАЗОВЫХ КОНФИГУРАЦИЙ ============
    
    # Базовые конфигурации для аналитики
    configs = [
        {
            'config_key': 'analytics_retention_days',
            'config_value': {'metrics': 90, 'sessions': 180, 'events': 30, 'reports': 365},
            'config_type': 'retention',
            'description': 'Периоды хранения аналитических данных в днях'
        },
        {
            'config_key': 'alert_thresholds',
            'config_value': {
                'blocked_messages_ratio': 0.2,
                'low_engagement_score': 0.3,
                'high_error_rate': 0.1,
                'long_inactivity_hours': 72
            },
            'config_type': 'thresholds',
            'description': 'Пороговые значения для генерации алертов'
        },
        {
            'config_key': 'report_schedules',
            'config_value': {
                'daily_report': {'enabled': True, 'time': '08:00'},
                'weekly_report': {'enabled': True, 'day': 'monday', 'time': '09:00'},
                'monthly_report': {'enabled': True, 'day': 1, 'time': '10:00'}
            },
            'config_type': 'schedules',
            'description': 'Расписание автоматической генерации отчетов'
        },
        {
            'config_key': 'engagement_calculation',
            'config_value': {
                'message_weight': 0.3,
                'session_weight': 0.4,
                'subject_weight': 0.3,
                'time_decay_factor': 0.9
            },
            'config_type': 'calculation',
            'description': 'Параметры расчета индекса вовлеченности'
        },
        {
            'config_key': 'safety_calculation',
            'config_value': {
                'blocked_penalty': 0.1,
                'moderation_bonus': 0.05,
                'time_window_days': 7,
                'min_messages_for_score': 10
            },
            'config_type': 'calculation',
            'description': 'Параметры расчета индекса безопасности'
        }
    ]
    
    # Вставляем конфигурации
    for config in configs:
        op.execute(sa.text("""
            INSERT INTO analytics_config (config_key, config_value, config_type, description)
            VALUES (:key, :value, :type, :description)
        """).bindparams(
            key=config['config_key'],
            value=json.dumps(config['config_value']),
            type=config['config_type'],
            description=config['description']
        ))
    
    # ============ ОБНОВЛЕНИЕ СТАТИСТИКИ ============
    op.execute("ANALYZE analytics_metrics")
    op.execute("ANALYZE user_sessions")
    op.execute("ANALYZE user_events")
    op.execute("ANALYZE analytics_reports")
    op.execute("ANALYZE analytics_trends")
    op.execute("ANALYZE analytics_alerts")
    op.execute("ANALYZE analytics_config")


def downgrade() -> None:
    """Удаление таблиц аналитики"""
    
    # Удаляем таблицы в обратном порядке
    op.drop_table('analytics_config')
    op.drop_table('analytics_alerts')
    op.drop_table('analytics_trends')
    op.drop_table('analytics_reports')
    op.drop_table('user_events')
    op.drop_table('user_sessions')
    op.drop_table('analytics_metrics')