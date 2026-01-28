"""
Модуль визуализации для математики.

Включает:
- Арифметика: таблицы умножения, сложения, вычитания, деления
- Алгебра: степени, формулы, свойства
- Геометрия: формулы площадей, объемов, классификация фигур
"""

from bot.services.visualization.math.algebra import AlgebraVisualization
from bot.services.visualization.math.arithmetic import ArithmeticVisualization
from bot.services.visualization.math.geometry import GeometryVisualization

__all__ = ["ArithmeticVisualization", "AlgebraVisualization", "GeometryVisualization"]
