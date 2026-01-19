"""
Подмодуль с вспомогательными детекторами для визуализаций.

Сейчас содержит:
- tables_and_diagrams: детекция таблиц, диаграмм, карт и графиков.
"""

from .tables_and_diagrams import detect_subject_tables_and_diagrams

__all__ = ["detect_subject_tables_and_diagrams"]
