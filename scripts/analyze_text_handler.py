"""
Анализ структуры text.py для разбиения.
"""
import re

with open('bot/handlers/ai_chat/text.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим все функции
functions = []
for match in re.finditer(r'^(async def|def) (\w+)', content, re.MULTILINE):
    start = match.start()
    name = match.group(2)
    functions.append((start, name, match.group(1)))

# Добавляем конец файла
functions.append((len(content), 'EOF', ''))

# Выводим размеры функций
print('Functions in text.py:')
for i in range(len(functions) - 1):
    start, name, func_type = functions[i]
    end, _, _ = functions[i + 1]
    lines = content[start:end].count('\n')
    print(f'{func_type} {name}: {lines} lines')

print(f'\nTotal: {len(functions) - 1} functions')
