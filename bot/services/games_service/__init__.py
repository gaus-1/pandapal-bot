"""
Сервис игр для PandaPalGo.
Реализует логику игр: крестики-нолики, шашки, 2048, эрудит.
Включает AI противника (панда) для игры с ребенком.
"""

from bot.services.game_ai import TicTacToeAI
from bot.services.games_service.checkers import CheckersMixin
from bot.services.games_service.erudite import EruditeMixin
from bot.services.games_service.game_2048 import Game2048Mixin
from bot.services.games_service.session import GamesServiceBase
from bot.services.games_service.tic_tac_toe import TicTacToeMixin


class GamesService(
    GamesServiceBase,
    TicTacToeMixin,
    CheckersMixin,
    Game2048Mixin,
    EruditeMixin,
):
    """Сервис для управления играми."""

    pass


__all__ = ["GamesService", "TicTacToeAI"]
