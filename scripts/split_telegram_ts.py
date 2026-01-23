"""
Разбиение telegram.ts на auth и utils.
"""

with open('frontend/src/services/telegram.ts', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим границы класса TelegramService
class_start = content.find('class TelegramService {')
class_end = content.rfind('}')

# Извлекаем импорты и класс
imports_end = content.find('class TelegramService {')
imports = content[:imports_end].rstrip()
telegram_class = content[class_start:class_end+1]

# Создаем основной файл (telegram.ts)
with open('frontend/src/services/telegram_new.ts', 'w', encoding='utf-8') as f:
    f.write(imports + '\n\n' + telegram_class + '\n\nexport const telegram = new TelegramService();\n')
    print('telegram_new.ts created')

print('Split completed!')
