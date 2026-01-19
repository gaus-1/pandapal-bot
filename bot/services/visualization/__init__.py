"""
Модуль визуализации для генерации графиков и таблиц по школьным предметам.

Архитектура:
- base.py: Базовый класс с общими методами (SOLID: SRP, DIP)
- schemes.py: Методы генерации специализированных схем (SOLID: SRP)
- detector.py: Логика детекции запросов (SOLID: SRP)
- math/: Математика, алгебра, геометрия
- languages/: Русский и английский языки
- sciences/: Физика и химия
- social/: История, география, обществознание
- other/: Окружающий мир, информатика

Принципы:
- PEP 20: "Simple is better than complex", "Flat is better than nested"
- SOLID: Single Responsibility, Open/Closed, Dependency Inversion
"""

from bot.services.visualization.base import BaseVisualizationService
from bot.services.visualization.detector import VisualizationDetector

__all__ = ["BaseVisualizationService", "VisualizationDetector"]
