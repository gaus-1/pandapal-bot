"""
Скрипт для разбиения api.ts на модули.
"""

# Читаем исходный файл
with open('frontend/src/services/api.ts', 'r', encoding='utf-8') as f:
    content = f.read()

# Chat API (строки 207-312)
chat_start = content.find('export async function sendAIMessage(')
chat_end = content.find('export async function getSubjects():')
chat_content = content[chat_start:chat_end].rstrip()

with open('frontend/src/services/api/chat.ts', 'w', encoding='utf-8') as f:
    f.write('''/**
 * API для чата с AI.
 */

import { API_BASE_URL } from './config';
import type { AchievementUnlocked } from './types';

''' + chat_content)
    print('chat.ts created')

# Games API (строки 359-555)
games_start = content.find('export interface GameSession {')
games_end = content.find('export async function createPremiumPayment(')
games_content = content[games_start:games_end].rstrip()

with open('frontend/src/services/api/games.ts', 'w', encoding='utf-8') as f:
    f.write('''/**
 * API для игр.
 */

import { API_BASE_URL } from './config';

''' + games_content)
    print('games.ts created')

# Premium API (строки 557-конец)
premium_start = content.find('export async function createPremiumPayment(')
premium_content = content[premium_start:].rstrip()

with open('frontend/src/services/api/premium.ts', 'w', encoding='utf-8') as f:
    f.write('''/**
 * API для премиум подписки.
 */

import { API_BASE_URL } from './config';

''' + premium_content)
    print('premium.ts created')

print('All API modules created!')
