"""Модуль визуализации для информатики."""

from bot.services.visualization.base import BaseVisualizationService


class ComputerScienceVisualization(BaseVisualizationService):
    """Визуализация для информатики: системы счисления."""

    def generate_number_systems_table(self) -> bytes | None:
        """Генерирует таблицу систем счисления."""
        headers = ["Система", "Основание", "Цифры", "Пример"]
        rows = [
            ["Двоичная", "2", "0, 1", "1010₂ = 10₁₀"],
            ["Восьмеричная", "8", "0-7", "12₈ = 10₁₀"],
            ["Десятичная", "10", "0-9", "10₁₀ = 10₁₀"],
            ["Шестнадцатеричная", "16", "0-9, A-F", "A₁₆ = 10₁₀"],
        ]
        return self.generate_table(headers, rows, "Системы счисления")
