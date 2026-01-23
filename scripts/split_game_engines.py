"""
Скрипт для разбиения game_engines.py на отдельные файлы.
"""

# Читаем исходный файл
with open('bot/services/game_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим классы
checkers_start = content.find('class CheckersGame:')
game2048_start = content.find('class Game2048:')
erudite_start = content.find('class EruditeGame:')

# Извлекаем классы
checkers = content[checkers_start:game2048_start].rstrip()
game2048 = content[game2048_start:erudite_start].rstrip()
erudite = content[erudite_start:].rstrip()

# Создаем файлы
with open('bot/services/game_engines/checkers.py', 'w', encoding='utf-8') as f:
    f.write('"""\nЛогика игры шашки.\n"""\n\n' + checkers)
    print('checkers.py created')

with open('bot/services/game_engines/game_2048.py', 'w', encoding='utf-8') as f:
    f.write('"""\nЛогика игры 2048.\n"""\n\nimport random\n\n' + game2048)
    print('game_2048.py created')

with open('bot/services/game_engines/erudite.py', 'w', encoding='utf-8') as f:
    f.write('"""\nЛогика игры Эрудит (Scrabble).\n"""\n\nimport random\n\n' + erudite)
    print('erudite.py created')

print('All files created successfully!')
