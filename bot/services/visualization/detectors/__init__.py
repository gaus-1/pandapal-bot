"""
Подмодуль с вспомогательными детекторами для визуализаций.

Содержит:
- request_words: списки ключевых слов для визуализации и объяснений.
- schemes: детекция специализированных схем.
- diagrams: детекция универсальных диаграмм.
- tables_and_diagrams: детекция предметных таблиц и хронологий.
- maps: детекция карт (города, страны, районы).
- physics: детекция физических графиков и схем.
- math_graphs: детекция математических графиков функций.
"""

from .diagrams import detect_diagram
from .maps import detect_map
from .math_graphs import detect_math_graph
from .physics import detect_physics
from .request_words import EXPLANATION_REQUEST_WORDS, VISUALIZATION_REQUEST_WORDS
from .schemes import detect_scheme
from .tables_and_diagrams import detect_subject_tables_and_diagrams

__all__ = [
    "VISUALIZATION_REQUEST_WORDS",
    "EXPLANATION_REQUEST_WORDS",
    "detect_scheme",
    "detect_diagram",
    "detect_subject_tables_and_diagrams",
    "detect_map",
    "detect_physics",
    "detect_math_graph",
]
