"""
Источник шуток из JokeAPI (если доступен из России).

Endpoint: https://v2.jokeapi.dev/joke/Any?safe-mode
"""

from typing import Any

from loguru import logger

from bot.services.news.sources.base import BaseNewsSource


class JokeAPISource(BaseNewsSource):
    """
    Источник шуток из JokeAPI.

    Использует safe-mode для детского контента.
    Fallback на локальную базу, если API недоступен.
    """

    def __init__(self):
        """Инициализация источника."""
        super().__init__(timeout=10.0, max_retries=2)
        self.base_url = "https://v2.jokeapi.dev/joke"

    def get_source_name(self) -> str:
        """Получить название источника."""
        return "joke_api"

    async def fetch_news(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Получить шутки из JokeAPI.

        Args:
            limit: Максимальное количество шуток

        Returns:
            List[dict]: Список шуток
        """
        jokes = []
        try:
            for _ in range(limit):
                try:
                    params = {
                        "safe-mode": "",
                        "type": "single,twopart",
                    }

                    data = await self._fetch_with_retry(f"{self.base_url}/Any", params=params)

                    if data.get("error"):
                        logger.warning(f"⚠️ JokeAPI вернул ошибку: {data.get('message')}")
                        break

                    # Проверяем флаги безопасности
                    flags = data.get("flags", {})
                    if flags.get("nsfw") or flags.get("religious") or flags.get("political"):
                        continue

                    if data.get("type") == "single":
                        joke_text = data.get("joke", "")
                    elif data.get("type") == "twopart":
                        setup = data.get("setup", "")
                        delivery = data.get("delivery", "")
                        joke_text = f"{setup}\n{delivery}"
                    else:
                        continue

                    if joke_text:
                        jokes.append(
                            {
                                "title": "Шутка",
                                "content": joke_text,
                                "url": None,
                                "source": self.get_source_name(),
                                "published_date": None,
                                "image_url": None,
                            }
                        )

                except Exception as e:
                    logger.warning(f"⚠️ Ошибка получения шутки из JokeAPI: {e}")
                    # Если API недоступен, прекращаем попытки
                    break

            logger.info(f"✅ Получено {len(jokes)} шуток из JokeAPI")
            return jokes

        except Exception as e:
            logger.warning(f"⚠️ JokeAPI недоступен из России или ошибка: {e}")
            return []
