"""
Сервис для работы с Yandex Translate API.

Обеспечивает перевод текста для изучения иностранных языков.
Поддерживает: английский, немецкий, французский, испанский.
"""

import httpx
from loguru import logger

from bot.config.settings import settings


class TranslateService:
    """
    Сервис для работы с Yandex Translate API.

    Возможности:
    - Перевод текста между языками
    - Определение языка текста
    - Поддержка школьных языков (английский, немецкий, французский, испанский)
    """

    # Поддерживаемые языки для школьников
    SUPPORTED_LANGUAGES = {
        "ru": "Русский",
        "en": "Английский",
        "de": "Немецкий",
        "fr": "Французский",
        "es": "Испанский",
    }

    def __init__(self):
        """Инициализация сервиса Yandex Translate."""
        self.api_key = settings.yandex_cloud_api_key
        self.folder_id = settings.yandex_cloud_folder_id

        # Endpoint Yandex Translate API
        self.translate_url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
        self.detect_url = "https://translate.api.cloud.yandex.net/translate/v2/detect"

        # Заголовки для запросов
        self.headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        # Таймаут для запросов
        self.timeout = httpx.Timeout(10.0, connect=5.0)

        logger.info("✅ TranslateService инициализирован")

    async def translate_text(
        self,
        text: str,
        target_language: str = "ru",
        source_language: str | None = None,
    ) -> str | None:
        """
        Переводит текст на целевой язык.

        Args:
            text: Текст для перевода
            target_language: Целевой язык (ru, en, de, fr, es)
            source_language: Исходный язык (если None - автоопределение)

        Returns:
            Переведенный текст или None при ошибке
        """
        try:
            if not text or not text.strip():
                logger.warning("Пустой текст для перевода")
                return None

            # Проверяем поддержку языка
            if target_language not in self.SUPPORTED_LANGUAGES:
                logger.warning(f"Неподдерживаемый язык: {target_language}")
                return None

            # Формируем запрос
            payload = {
                "folderId": self.folder_id,
                "texts": [text],
                "targetLanguageCode": target_language,
            }

            # Добавляем исходный язык если указан
            if source_language:
                payload["sourceLanguageCode"] = source_language

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.translate_url, json=payload, headers=self.headers)

                if response.status_code != 200:
                    logger.error(
                        f"Ошибка Yandex Translate API: {response.status_code} - {response.text}"
                    )
                    return None

                data = response.json()

                # Извлекаем переведенный текст
                if "translations" in data and len(data["translations"]) > 0:
                    translated_text = data["translations"][0]["text"]
                    logger.info(f"✅ Перевод выполнен: {text[:50]}... → {translated_text[:50]}...")
                    return translated_text
                else:
                    logger.error("Нет перевода в ответе API")
                    return None

        except httpx.TimeoutException:
            logger.error("Таймаут при обращении к Yandex Translate API")
            return None
        except Exception as e:
            logger.error(f"Ошибка перевода текста: {e}")
            return None

    async def detect_language(self, text: str) -> str | None:
        """
        Определяет язык текста.

        Args:
            text: Текст для определения языка

        Returns:
            Код языка (ru, en, de, fr, es) или None при ошибке
        """
        try:
            if not text or not text.strip():
                return None

            payload = {
                "folderId": self.folder_id,
                "text": text,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.detect_url, json=payload, headers=self.headers)

                if response.status_code != 200:
                    logger.error(
                        f"Ошибка определения языка: {response.status_code} - {response.text}"
                    )
                    return None

                data = response.json()

                if "languageCode" in data:
                    language_code = data["languageCode"]
                    logger.info(f"✅ Язык определен: {language_code}")
                    return language_code
                else:
                    return None

        except Exception as e:
            logger.error(f"Ошибка определения языка: {e}")
            return None

    async def get_word_translations(
        self, word: str, from_lang: str = "en", to_lang: str = "ru"
    ) -> str | None:
        """
        Получает перевод слова с примерами использования.

        Args:
            word: Слово для перевода
            from_lang: Исходный язык
            to_lang: Целевой язык

        Returns:
            Форматированный ответ с переводом и примерами
        """
        try:
            # Переводим слово
            translation = await self.translate_text(word, to_lang, from_lang)

            if not translation:
                return None

            # Создаем примеры использования
            examples = await self._generate_usage_examples(word, from_lang)

            # Форматируем ответ
            from_lang_name = self.SUPPORTED_LANGUAGES.get(from_lang, from_lang)
            to_lang_name = self.SUPPORTED_LANGUAGES.get(to_lang, to_lang)

            response = (
                f"📚 Перевод:\n"
                f"{word} ({from_lang_name}) → {translation} ({to_lang_name})\n\n"
                f"💡 Примеры использования:\n{examples}"
            )

            return response

        except Exception as e:
            logger.error(f"Ошибка получения перевода слова: {e}")
            return None

    async def _generate_usage_examples(self, word: str, language: str) -> str:
        """Генерирует примеры использования слова (заглушка для будущего AI)."""
        # В будущем можно интегрировать с YandexGPT для генерации примеров
        # Пока возвращаем простой пример
        if language == "en":
            return f"• I like to {word.lower()}.\n• Can you {word.lower()}?"
        elif language == "de":
            return f"• Ich möchte {word.lower()}.\n• Das ist {word.lower()}."
        elif language == "fr":
            return f"• Je veux {word.lower()}.\n• C'est {word.lower()}."
        else:
            return f"• Пример 1 с {word}\n• Пример 2 с {word}"

    def get_supported_languages(self) -> list[str]:
        """Возвращает список поддерживаемых языков."""
        return list(self.SUPPORTED_LANGUAGES.keys())

    def get_language_name(self, code: str) -> str:
        """Возвращает название языка по коду."""
        return self.SUPPORTED_LANGUAGES.get(code, code)


# Singleton instance
_translate_service: TranslateService | None = None


def get_translate_service() -> TranslateService:
    """Получить singleton instance TranslateService."""
    global _translate_service
    if _translate_service is None:
        _translate_service = TranslateService()
    return _translate_service
