#!/usr/bin/env python3
"""
Тест AI сервиса для диагностики проблем
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_gemini_connection():
    """Тест подключения к Gemini API"""
    try:
        import google.generativeai as genai
        
        # Получаем API ключ
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY не найден в .env")
            return False
            
        print(f"✅ API ключ найден: {api_key[:10]}...")
        
        # Настраиваем Gemini
        genai.configure(api_key=api_key)
        
        # Тестируем модель
        model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
        print(f"🔧 Используем модель: {model_name}")
        
        model = genai.GenerativeModel(model_name)
        
        # Простой тест
        response = model.generate_content("Привет! Как дела?")
        
        if response.text:
            print(f"✅ AI ответил: {response.text[:100]}...")
            return True
        else:
            print("❌ AI не дал ответ")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Тестируем Gemini AI...")
    success = test_gemini_connection()
    
    if success:
        print("🎉 AI работает!")
    else:
        print("💥 AI не работает!")
        
    sys.exit(0 if success else 1)
