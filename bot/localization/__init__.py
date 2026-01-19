"""
Система интернационализации для PandaPal Bot.

Поддерживает русский и английский языки с возможностью
легкого добавления новых языков.
"""

import json
from pathlib import Path
from typing import Any

from loguru import logger


class LocalizationManager:
    """
    Менеджер интернационализации для PandaPal Bot.

    Загружает и управляет переводами для разных языков.
    """

    def __init__(self, locale_dir: str = "bot/localization/locales"):
        """
        Инициализация менеджера локализации.

        Args:
            locale_dir: Путь к директории с файлами переводов
        """
        self.locale_dir = Path(locale_dir)
        self.translations: dict[str, dict[str, Any]] = {}
        self.current_language = "ru"  # По умолчанию русский
        self.fallback_language = "en"  # Fallback на английский

        self._load_translations()

    def _load_translations(self):
        """Загрузка всех переводов."""
        if not self.locale_dir.exists():
            self._create_default_translations()
            return

        for locale_file in self.locale_dir.glob("*.json"):
            language = locale_file.stem
            try:
                with open(locale_file, encoding="utf-8") as f:
                    self.translations[language] = json.load(f)
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки переводов для {language}: {e}")

    def _create_default_translations(self):
        """Создание переводов по умолчанию."""
        self.locale_dir.mkdir(parents=True, exist_ok=True)

        # Русские переводы
        ru_translations = {
            "welcome": {
                "greeting": "Привет! Я PandaPal - твой образовательный помощник! 🐼",
                "help": "Я помогу тебе с уроками, поиграю в развивающие игры и отвечу на вопросы!",
                "start_learning": "Давайте начнем учиться! 📚",
            },
            "game": {
                "start": "Начать игру PandaPal Go! 🎮",
                "pause": "Пауза",
                "resume": "Продолжить",
                "level_complete": "Уровень пройден! 🎉",
                "game_over": "Игра окончена! Попробуй еще раз! 💪",
            },
            "math": {
                "solve_task": "Реши задачу:",
                "correct": "Правильно! 🎯",
                "incorrect": "Не совсем так. Попробуй еще раз! 🤔",
                "hint": "Подсказка: {hint}",
            },
            "errors": {
                "generic": "Произошла ошибка. Попробуй еще раз!",
                "network": "Проблемы с интернетом. Проверь соединение.",
                "rate_limit": "Слишком много запросов. Подожди немного.",
            },
        }

        # Английские переводы
        en_translations = {
            "welcome": {
                "greeting": "Hi! I'm PandaPal - your educational assistant! 🐼",
                "help": "I'll help you with lessons, play educational games, and answer questions!",
                "start_learning": "Let's start learning! 📚",
            },
            "game": {
                "start": "Start PandaPal Go game! 🎮",
                "pause": "Pause",
                "resume": "Resume",
                "level_complete": "Level completed! 🎉",
                "game_over": "Game over! Try again! 💪",
            },
            "math": {
                "solve_task": "Solve the task:",
                "correct": "Correct! 🎯",
                "incorrect": "Not quite right. Try again! 🤔",
                "hint": "Hint: {hint}",
            },
            "errors": {
                "generic": "An error occurred. Please try again!",
                "network": "Network issues. Check your connection.",
                "rate_limit": "Too many requests. Please wait a moment.",
            },
        }

        # Сохраняем переводы
        with open(self.locale_dir / "ru.json", "w", encoding="utf-8") as f:
            json.dump(ru_translations, f, ensure_ascii=False, indent=2)

        with open(self.locale_dir / "en.json", "w", encoding="utf-8") as f:
            json.dump(en_translations, f, ensure_ascii=False, indent=2)

        self.translations = {"ru": ru_translations, "en": en_translations}

    def set_language(self, language: str):
        """
        Установка текущего языка.

        Args:
            language: Код языка (ru, en, etc.)
        """
        if language in self.translations:
            self.current_language = language
        else:
            logger.warning(f"⚠️ Язык {language} не найден, используется {self.current_language}")

    def get_language(self) -> str:
        """
        Получение текущего языка.

        Returns:
            str: Код текущего языка
        """
        return self.current_language

    def translate(self, key: str, **kwargs) -> str:
        """
        Перевод ключа на текущий язык.

        Args:
            key: Ключ перевода (например, "welcome.greeting")
            **kwargs: Параметры для форматирования

        Returns:
            str: Переведенный текст
        """
        try:
            # Получаем перевод
            translation = self._get_nested_value(key, self.current_language)

            # Если перевод не найден, пробуем fallback язык
            if translation is None and self.current_language != self.fallback_language:
                translation = self._get_nested_value(key, self.fallback_language)

            # Если и fallback не найден, возвращаем ключ
            if translation is None:
                return f"[{key}]"

            # Форматируем строку с параметрами
            if kwargs:
                try:
                    return translation.format(**kwargs)
                except KeyError as e:
                    return f"[{key}] (missing param: {e})"

            return translation

        except Exception as e:
            logger.error(f"❌ Ошибка перевода ключа {key}: {e}")
            return f"[{key}]"

    def _get_nested_value(self, key: str, language: str) -> str | None:
        """
        Получение вложенного значения по ключу.

        Args:
            key: Ключ в формате "section.key"
            language: Язык

        Returns:
            Optional[str]: Значение или None
        """
        if language not in self.translations:
            return None

        value = self.translations[language]
        keys = key.split(".")

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None

        return value if isinstance(value, str) else None

    def get_available_languages(self) -> list:
        """
        Получение списка доступных языков.

        Returns:
            list: Список кодов языков
        """
        return list(self.translations.keys())

    def add_translation(self, language: str, key: str, value: str):
        """
        Добавление нового перевода.

        Args:
            language: Код языка
            key: Ключ перевода
            value: Значение перевода
        """
        if language not in self.translations:
            self.translations[language] = {}

        # Создаем вложенную структуру
        keys = key.split(".")
        current = self.translations[language]

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def save_translations(self):
        """Сохранение всех переводов в файлы."""
        for language, translations in self.translations.items():
            locale_file = self.locale_dir / f"{language}.json"
            with open(locale_file, "w", encoding="utf-8") as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)


# Глобальный экземпляр менеджера локализации
_localization_manager: LocalizationManager | None = None


def get_localization_manager() -> LocalizationManager:
    """
    Получить глобальный экземпляр менеджера локализации.

    Returns:
        LocalizationManager: Экземпляр менеджера
    """
    global _localization_manager

    if _localization_manager is None:
        _localization_manager = LocalizationManager()

    return _localization_manager


def t(key: str, **kwargs) -> str:
    """
    Быстрый перевод ключа.

    Args:
        key: Ключ перевода
        **kwargs: Параметры для форматирования

    Returns:
        str: Переведенный текст
    """
    manager = get_localization_manager()
    return manager.translate(key, **kwargs)


def set_language(language: str):
    """
    Быстрая установка языка.

    Args:
        language: Код языка
    """
    manager = get_localization_manager()
    manager.set_language(language)


# Инициализация при импорте
if __name__ != "__main__":
    get_localization_manager()
