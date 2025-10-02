#!/usr/bin/env python3
"""
Скрипт для очистки webhook и решения конфликта экземпляров бота
"""

import requests
import os
from bot.config import settings

def clear_webhook():
    """Очищает webhook для решения конфликта экземпляров"""
    bot_token = settings.telegram_bot_token
    url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    
    print("🔄 Очищаем webhook...")
    
    try:
        response = requests.post(url, data={"drop_pending_updates": True})
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("✅ Webhook успешно очищен!")
                print(f"📝 Ответ: {result.get('description', 'OK')}")
            else:
                print(f"❌ Ошибка: {result.get('description', 'Unknown error')}")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка при очистке webhook: {e}")

def get_bot_info():
    """Получает информацию о боте"""
    bot_token = settings.telegram_bot_token
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    
    print("🔍 Получаем информацию о боте...")
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                bot_info = result.get("result", {})
                print(f"✅ Бот: @{bot_info.get('username', 'Unknown')}")
                print(f"📝 Имя: {bot_info.get('first_name', 'Unknown')}")
                print(f"🆔 ID: {bot_info.get('id', 'Unknown')}")
            else:
                print(f"❌ Ошибка: {result.get('description', 'Unknown error')}")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка при получении информации: {e}")

if __name__ == "__main__":
    print("🚀 PandaPal Bot - Очистка конфликта экземпляров")
    print("=" * 50)
    
    get_bot_info()
    print()
    clear_webhook()
    
    print("\n🎯 Теперь Render сможет запустить бота без конфликтов!")
