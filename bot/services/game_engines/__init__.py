"""
Game Engines - чистая логика игр без зависимостей от фреймворков.

Этот модуль реэкспортирует все игровые движки для обратной совместимости.
"""

from .checkers import CheckersGame
from .erudite import EruditeGame
from .game_2048 import Game2048
from .tic_tac_toe import TicTacToe

__all__ = [
    "TicTacToe",
    "CheckersGame",
    "Game2048",
    "EruditeGame",
]
