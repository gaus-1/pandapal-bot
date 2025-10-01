"""
Сервис для работы с Google Gemini AI
Обеспечивает общение с ИИ, адаптацию под возраст, память контекста
@module bot.services.ai_service
"""

import google.generativeai as genai
from typing import Optional, List, Dict
from loguru import logger

from bot.config import settings, AI_SYSTEM_PROMPT
from bot.services.moderation_service import ContentModerationService


class GeminiAIService:
    """
    Сервис для работы с Google Gemini AI
    
    Возможности:
    - Генерация текстовых ответов с учётом контекста (50 последних сообщений)
    - Адаптация под возраст ребёнка
    - Модерация контента (входящего и исходящего)
    - Генерация решений задач, объяснений, примеров
    """
    
    def __init__(self):
        """
        Инициализация Gemini AI
        Настройка API ключа и модели
        """
        # Конфигурация Gemini API
        genai.configure(api_key=settings.gemini_api_key)
        
        # Настройки генерации
        self.generation_config = {
            'temperature': settings.ai_temperature,
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': settings.ai_max_tokens,
        }
        
        # Настройки безопасности Gemini (блокировка опасного контента)
        self.safety_settings = [
            {
                'category': 'HARM_CATEGORY_HARASSMENT',
                'threshold': 'BLOCK_MEDIUM_AND_ABOVE'  # Блокируем harassment
            },
            {
                'category': 'HARM_CATEGORY_HATE_SPEECH',
                'threshold': 'BLOCK_MEDIUM_AND_ABOVE'  # Блокируем hate speech
            },
            {
                'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
                'threshold': 'BLOCK_MEDIUM_AND_ABOVE'  # Блокируем 18+ контент
            },
            {
                'category': 'HARM_CATEGORY_DANGEROUS_CONTENT',
                'threshold': 'BLOCK_MEDIUM_AND_ABOVE'  # Блокируем опасный контент
            },
        ]
        
        # Инициализация модели
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
            system_instruction=AI_SYSTEM_PROMPT  # Системный промпт PandaPalAI
        )
        
        # Сервис модерации
        self.moderation = ContentModerationService()
        
        logger.info(f"✅ Gemini AI инициализирован: модель {settings.gemini_model}")
    
    async def generate_response(
        self,
        user_message: str,
        chat_history: List[Dict[str, str]] = None,
        user_age: Optional[int] = None,
        user_grade: Optional[int] = None
    ) -> str:
        """
        Генерация ответа AI с учётом контекста и возраста
        
        Args:
            user_message: Сообщение от пользователя
            chat_history: История чата (последние 50 сообщений)
            user_age: Возраст ребёнка (для адаптации языка)
            user_grade: Класс (для адаптации сложности)
        
        Returns:
            str: Ответ от AI
        
        Raises:
            ValueError: Если контент заблокирован модерацией
        """
        try:
            # ШАГ 1: Модерация входящего сообщения
            is_safe, reason = self.moderation.is_safe_content(user_message)
            
            if not is_safe:
                logger.warning(f"🚫 Заблокировано сообщение: {reason}")
                self.moderation.log_blocked_content(0, user_message, reason)
                
                # Возвращаем дружелюбный отказ
                return self.moderation.get_safe_response_alternative(reason)
            
            # ШАГ 2: Подготовка контекста (возраст и класс)
            context_instruction = self._build_context_instruction(user_age, user_grade)
            
            # ШАГ 3: Формирование промпта с контекстом
            full_message = f"{context_instruction}\n\nВопрос ребёнка: {user_message}"
            
            # ШАГ 4: Создание чата с историей
            if chat_history:
                # Используем историю для контекста
                chat = self.model.start_chat(history=chat_history)
                response = chat.send_message(full_message)
            else:
                # Первое сообщение без истории
                response = self.model.generate_content(full_message)
            
            # Извлекаем текст ответа
            ai_response = response.text
            
            # ШАГ 5: Модерация ответа AI (дополнительная проверка)
            ai_response = self.moderation.sanitize_ai_response(ai_response)
            
            logger.info(f"🤖 AI ответил (длина: {len(ai_response)} символов)")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации AI: {e}")
            
            # Безопасный fallback ответ при ошибке
            return (
                "Ой, кажется у меня технические проблемы 🔧 "
                "Попробуй спросить чуть позже или перефразируй вопрос!"
            )
    
    def _build_context_instruction(
        self, 
        age: Optional[int], 
        grade: Optional[int]
    ) -> str:
        """
        Построение инструкции с учётом возраста и класса
        Адаптирует сложность и стиль ответа
        
        Args:
            age: Возраст ребёнка
            grade: Класс
        
        Returns:
            str: Дополнительная инструкция для AI
        """
        context_parts = []
        
        if age:
            if age <= 10:
                context_parts.append(
                    "Ребёнку 6-10 лет. Используй ОЧЕНЬ простой язык, "
                    "короткие предложения, много примеров из повседневной жизни."
                )
            elif age <= 13:
                context_parts.append(
                    "Ребёнку 11-13 лет. Используй понятный язык, "
                    "можно чуть более сложные термины, но объясняй их."
                )
            else:
                context_parts.append(
                    "Подростку 14-18 лет. Можешь использовать более "
                    "академический язык, но оставайся дружелюбным."
                )
        
        if grade:
            context_parts.append(
                f"Ученик {grade} класса. Ориентируйся на программу {grade} класса."
            )
        
        if context_parts:
            return "КОНТЕКСТ: " + " ".join(context_parts)
        
        return ""
    
    async def explain_topic(
        self,
        topic: str,
        subject: str,
        grade: Optional[int] = None
    ) -> str:
        """
        Объяснить учебную тему
        
        Args:
            topic: Тема для объяснения
            subject: Предмет (математика, физика и т.д.)
            grade: Класс (для адаптации сложности)
        
        Returns:
            str: Объяснение темы
        """
        prompt = f"""
Объясни тему "{topic}" по предмету "{subject}" для ученика {grade or 5} класса.

Требования:
1. Простым и понятным языком
2. С примерами из жизни
3. Пошагово, от простого к сложному
4. Добавь практические задачи для закрепления (2-3 штуки)

Формат ответа:
📚 Что это такое
🔍 Как это работает
💡 Примеры из жизни
✏️ Практические задачи
"""
        return await self.generate_response(prompt, user_grade=grade)
    
    async def solve_problem(
        self,
        problem_text: str,
        subject: str,
        show_steps: bool = True
    ) -> str:
        """
        Решить задачу с пошаговым объяснением
        
        Args:
            problem_text: Текст задачи
            subject: Предмет
            show_steps: Показывать шаги решения
        
        Returns:
            str: Решение с объяснением
        """
        prompt = f"""
Реши задачу по предмету "{subject}":

{problem_text}

{'Покажи ПОДРОБНОЕ пошаговое решение с объяснением каждого шага.' if show_steps else 'Покажи только ответ и краткое объяснение.'}

Формат:
📝 Условие (кратко перескажи что дано)
🔢 Решение (пошагово)
✅ Ответ
💡 Почему так (объясни логику)
"""
        return await self.generate_response(prompt)
    
    async def check_answer(
        self,
        problem: str,
        user_answer: str,
        correct_answer: Optional[str] = None
    ) -> str:
        """
        Проверить ответ ученика и дать фидбек
        
        Args:
            problem: Условие задачи
            user_answer: Ответ ученика
            correct_answer: Правильный ответ (если известен)
        
        Returns:
            str: Фидбек с объяснением
        """
        prompt = f"""
Задача: {problem}

Ответ ученика: {user_answer}
{f'Правильный ответ: {correct_answer}' if correct_answer else ''}

Проверь ответ ученика:
1. Правильный ли ответ?
2. Если правильный — похвали и объясни почему
3. Если неправильный — объясни ошибку МЯГКО и подскажи как исправить
4. Дай совет как решать подобные задачи

Будь добрым и поддерживающим! 🐼
"""
        return await self.generate_response(prompt)
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Получить информацию о модели (для отладки)
        НЕ РАСКРЫВАТЬ пользователям!
        
        Returns:
            Dict: Информация о модели и настройках
        """
        return {
            'model': settings.gemini_model,
            'temperature': str(settings.ai_temperature),
            'max_tokens': str(settings.ai_max_tokens),
            'public_name': 'PandaPalAI',  # То, что видят пользователи
        }

