"""Модуль визуализации для окружающего мира."""

from bot.services.visualization.base import BaseVisualizationService


class WorldAroundVisualization(BaseVisualizationService):
    """Визуализация для окружающего мира: времена года, месяцы, природные зоны."""

    def generate_seasons_months_table(self) -> bytes | None:
        """Генерирует таблицу времен года, месяцев, дней недели."""
        headers = ["Время года", "Месяцы", "Дни недели"]
        rows = [
            ["Зима", "декабрь, январь, февраль", "понедельник, вторник"],
            ["Весна", "март, апрель, май", "среда, четверг"],
            ["Лето", "июнь, июль, август", "пятница, суббота"],
            ["Осень", "сентябрь, октябрь, ноябрь", "воскресенье"],
        ]
        return self.generate_table(headers, rows, "Времена года, месяцы, дни недели")
