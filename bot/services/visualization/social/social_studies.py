"""Модуль визуализации для обществознания."""

from bot.services.visualization.base import BaseVisualizationService


class SocialStudiesVisualization(BaseVisualizationService):
    """Визуализация для обществознания: ветви власти, государство."""

    def generate_government_branches_table(self) -> bytes | None:
        """Генерирует таблицу ветвей власти."""
        headers = ["Ветвь власти", "Функции", "Органы"]
        rows = [
            ["Законодательная", "Принятие законов", "Государственная Дума, Совет Федерации"],
            ["Исполнительная", "Исполнение законов", "Правительство, министерства"],
            ["Судебная", "Правосудие", "Верховный суд, Конституционный суд"],
        ]
        return self.generate_table(headers, rows, "Ветви власти в России")
