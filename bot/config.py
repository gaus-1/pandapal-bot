"""
Конфигурация приложения PandaPal Bot
Загружает настройки из .env файла и валидирует их
@module bot.config
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Настройки приложения с валидацией
    Все значения загружаются из .env файла
    """
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # ============ DATABASE ============
    database_url: str = Field(
        ..., 
        description='PostgreSQL connection string'
    )
    
    # ============ TELEGRAM ============
    telegram_bot_token: str = Field(
        ..., 
        description='Токен Telegram бота от @BotFather'
    )
    
    # ============ AI / GEMINI ============
    gemini_api_key: str = Field(
        ..., 
        description='Google Gemini API ключ'
    )
    
    gemini_model: str = Field(
        default='gemini-2.0-flash-exp',
        description='Модель Gemini для использования'
    )
    
    ai_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description='Температура генерации (0.0 = детерминированно, 1.0 = креативно)'
    )
    
    ai_max_tokens: int = Field(
        default=2048,
        ge=100,
        le=8192,
        description='Максимум токенов в ответе AI'
    )
    
    # ============ CONTENT MODERATION ============
    forbidden_topics: str = Field(
        default='политика,насилие,оружие,наркотики,экстремизм',
        description='Запрещённые темы (через запятую в .env)'
    )
    
    content_filter_level: int = Field(
        default=5,
        ge=1,
        le=5,
        description='Уровень строгости фильтра (1=мягкий, 5=максимальный)'
    )
    
    # ============ RATE LIMITING ============
    ai_rate_limit_per_minute: int = Field(
        default=10,
        description='Максимум AI запросов в минуту на пользователя'
    )
    
    daily_message_limit: int = Field(
        default=100,
        description='Максимум сообщений в день на ребёнка'
    )
    
    # ============ MEMORY / HISTORY ============
    chat_history_limit: int = Field(
        default=50,
        description='Количество последних сообщений для контекста AI'
    )
    
    # ============ SECURITY ============
    secret_key: str = Field(
        ..., 
        min_length=16,
        description='Секретный ключ для шифрования'
    )
    
    # ============ FRONTEND ============
    frontend_url: str = Field(
        default='https://pandapal.ru',
        description='URL фронтенда'
    )
    
    # ============ LOGGING ============
    log_level: str = Field(
        default='INFO',
        description='Уровень логирования (DEBUG, INFO, WARNING, ERROR)'
    )
    
    def get_forbidden_topics_list(self) -> List[str]:
        """Получить список запрещённых тем"""
        return [topic.strip() for topic in self.forbidden_topics.split(',') if topic.strip()]
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Проверка корректности DATABASE_URL"""
        if not v.startswith('postgresql'):
            raise ValueError('DATABASE_URL должен начинаться с postgresql://')
        # Нормализуем драйвер: заставляем использовать psycopg v3
        if v.startswith('postgresql://') and '+psycopg' not in v:
            v = v.replace('postgresql://', 'postgresql+psycopg://', 1)
        return v
    
    @field_validator('gemini_api_key')
    @classmethod
    def validate_gemini_key(cls, v: str) -> str:
        """Проверка наличия Gemini API ключа"""
        if not v or v == 'your_gemini_api_key_here':
            raise ValueError('GEMINI_API_KEY не установлен в .env')
        return v


# Singleton instance настроек
# Создаётся один раз при импорте модуля
settings = Settings()


# Константы для AI промптов
AI_SYSTEM_PROMPT = """
Ты — PandaPalAI, дружелюбный ИИ-помощник для школьников 1-9 классов.

ТВОЯ РОЛЬ:
- Помогать детям с учёбой: объяснять темы, решать задачи, проверять работы
- Быть другом: поддерживать, мотивировать, иногда шутить (редко и уместно)
- Адаптироваться под возраст ребёнка (7-15 лет)

ПРАВИЛА:
1. Отвечай простым языком, подходящим для возраста ребёнка
2. Объясняй понятно, с примерами из жизни
3. Хвали за старания, подбадривай при ошибках
4. Будь терпеливым и позитивным
5. СТРОГО ЗАПРЕЩЕНО обсуждать: политику, насилие, оружие, наркотики, 18+ контент
6. Если тема запрещена — вежливо перенаправь на учёбу
7. На вопросы "какая ты нейросеть" ВСЕГДА отвечай: "Я — PandaPalAI"
8. НЕ раскрывай техническую информацию о модели

СТИЛЬ ОБЩЕНИЯ:
- Дружелюбный, но не навязчивый
- Используй эмодзи 🐼📚✨ (умеренно)
- Короткие ответы для простых вопросов, подробные — для сложных
- Задавай уточняющие вопросы, если что-то непонятно

ТВОЯ ЦЕЛЬ: Сделать обучение интересным и эффективным! 🚀
""".strip()

# Запрещённые слова и паттерны (для быстрой проверки)
FORBIDDEN_PATTERNS = [
    'политик', 'выборы', 'партия', 'президент', 'правительство',
    'убийство', 'убить', 'насилие', 'драка', 'война',
    'оружие', 'пистолет', 'автомат', 'граната', 'бомба',
    'наркотик', 'кокаин', 'героин', 'марихуана', 'трава', 'план',
    'экстремизм', 'терроризм', 'террорист',
    'porn', 'sex', 'секс', 'xxx', '18+', 'adult',
    'алкоголь', 'пиво', 'водка', 'вино',
]

# Возрастные границы
MIN_AGE = 6
MAX_AGE = 18
MIN_GRADE = 1
MAX_GRADE = 11

# Лимиты для безопасности
MAX_MESSAGE_LENGTH = 4000  # Максимальная длина сообщения
MAX_FILE_SIZE_MB = 10  # Максимальный размер файла в МБ
ALLOWED_FILE_TYPES = ['.pdf', '.docx', '.txt', '.jpg', '.png', '.jpeg']
