"""
Анализ test_subjects_real_api.py для разбиения по предметам.
"""
import re

with open('tests/integration/test_subjects_real_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим все тесты
tests = []
for match in re.finditer(r'^(async def|def) (test_\w+)', content, re.MULTILINE):
    name = match.group(2)
    tests.append(name)

print(f'Total tests: {len(tests)}')
print('\nTests by subject:')

# Группируем по предметам
subjects = {}
for test in tests:
    # Извлекаем предмет из имени теста
    for subject in ['math', 'russian', 'english', 'physics', 'chemistry', 'biology', 'history', 'geography', 'literature']:
        if subject in test.lower():
            if subject not in subjects:
                subjects[subject] = []
            subjects[subject].append(test)
            break

for subject, test_list in sorted(subjects.items()):
    print(f'\n{subject.upper()}: {len(test_list)} tests')
    for test in test_list[:3]:
        print(f'  - {test}')
    if len(test_list) > 3:
        print(f'  ... и еще {len(test_list) - 3}')
