"""
Скрипт для извлечения классов из bot/models.py
"""
import re

# Читаем файл
with open('bot/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Извлекаем импорты
imports_match = re.search(r'(""".*?""".*?from sqlalchemy.sql import func)', content, re.DOTALL)
imports = imports_match.group(1) if imports_match else ""

# Находим границы классов
classes = []
for match in re.finditer(r'^class (\w+)\(Base\):', content, re.MULTILINE):
    classes.append((match.start(), match.group(1)))

# Добавляем конец файла
classes.append((len(content), 'EOF'))

# Группируем классы по доменам
domains = {
    'chat': ['ChatHistory', 'DailyRequestCount'],
    'learning': ['LearningSession', 'ProblemTopic', 'HomeworkSubmission'],
    'analytics': ['AnalyticsMetric'],
    'payments': ['Subscription', 'Payment'],
    'games': ['GameSession', 'GameStats'],
}

# Извлекаем классы
class_contents = {}
for i in range(len(classes) - 1):
    start, name = classes[i]
    end, _ = classes[i + 1]
    class_content = content[start:end].rstrip()
    class_contents[name] = class_content
    lines = class_content.count('\n')
    print(f'{name}: {lines} строк')

print(f'\nВсего классов: {len(class_contents)}')
