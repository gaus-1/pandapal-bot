"""
Скрипт для разбиения games_service.py на AI и сервис.
"""

# Читаем исходный файл
with open('bot/services/games_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим классы
imports_end = content.find('def _debug_log(')
tictactoe_ai_start = content.find('class TicTacToeAI:')
checkers_ai_start = content.find('class CheckersAI:')
games_service_start = content.find('class GamesService:')

# Извлекаем части
imports = content[:imports_end].rstrip()
debug_log = content[imports_end:tictactoe_ai_start].rstrip()
tictactoe_ai = content[tictactoe_ai_start:checkers_ai_start].rstrip()
checkers_ai = content[checkers_ai_start:games_service_start].rstrip()
games_service = content[games_service_start:].rstrip()

# Создаем AI файл
with open('bot/services/game_ai.py', 'w', encoding='utf-8') as f:
    f.write(imports + '\n\n' + debug_log + '\n\n\n' + tictactoe_ai + '\n\n\n' + checkers_ai)
    print('game_ai.py created')

# Создаем сервис файл
with open('bot/services/games_service_new.py', 'w', encoding='utf-8') as f:
    f.write(imports + '\n\nfrom bot.services.game_ai import CheckersAI, TicTacToeAI\n\n' + games_service)
    print('games_service_new.py created')

print('Split completed!')
