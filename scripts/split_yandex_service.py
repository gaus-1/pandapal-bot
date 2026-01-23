"""
Разбиение yandex_cloud_service.py на GPT, STT, Vision.
"""
import re

with open('bot/services/yandex_cloud_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим методы класса
methods = []
for match in re.finditer(r'^\s{4}(async def|def) (\w+)', content, re.MULTILINE):
    start = match.start()
    name = match.group(2)
    methods.append((start, name))

# Группируем методы по функциональности
print('Methods in YandexCloudService:')
for start, name in methods:
    print(f'  {name}')

# Определяем группы
gpt_methods = ['_get_iam_token', 'generate_text', 'generate_stream']
stt_methods = ['transcribe_audio']
vision_methods = ['analyze_image']

print('\nGPT methods:', gpt_methods)
print('STT methods:', stt_methods)
print('Vision methods:', vision_methods)
