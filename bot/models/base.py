"""
Базовый класс для всех моделей SQLAlchemy.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей SQLAlchemy.

    Все модели приложения наследуются от этого класса для обеспечения
    единообразной структуры и поведения.
    """

    pass
