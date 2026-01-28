"""
Настройки для новостного бота.

Отдельная конфигурация для новостного бота с валидацией через Pydantic.
"""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NewsBotSettings(BaseSettings):
    """
    Настройки новостного бота.

    Загружает параметры из переменных окружения.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    news_bot_token: str = Field(
        default="",
        description="Токен Telegram бота для новостей от @BotFather",
        validation_alias=AliasChoices("NEWS_BOT_TOKEN", "news_bot_token"),
    )

    news_bot_webhook_domain: str = Field(
        default="pandapal-bot-production.up.railway.app",
        description="Домен для webhook новостного бота (без https://)",
        validation_alias=AliasChoices("NEWS_BOT_WEBHOOK_DOMAIN", "news_bot_webhook_domain"),
    )

    news_bot_enabled: bool = Field(
        default=False,
        description="Включен ли новостной бот (для варианта с одним сервисом)",
        validation_alias=AliasChoices("NEWS_BOT_ENABLED", "news_bot_enabled"),
    )

    news_collection_enabled: bool = Field(
        default=False,
        description="Включен ли сбор новостей в БД (можно true без NEWS_BOT_ENABLED)",
        validation_alias=AliasChoices("NEWS_COLLECTION_ENABLED", "news_collection_enabled"),
    )

    # Используем те же настройки БД и Yandex Cloud из основного settings
    # Эти поля не обязательны здесь, так как используются из основного settings

    # API ключи для новостных источников
    world_news_api_key: str = Field(
        default="0e70d6a927c547c3878bdd85b72e3232",
        description="API ключ World News API",
        validation_alias=AliasChoices("WORLD_NEWS_API_KEY", "world_news_api_key"),
    )

    newsapi_key: str = Field(
        default="73663febf6264874b425c9b5b9ae0b08",
        description="API ключ NewsAPI.org",
        validation_alias=AliasChoices("NEWSAPI_KEY", "newsapi_key"),
    )


# Singleton instance настроек
news_bot_settings = NewsBotSettings()
