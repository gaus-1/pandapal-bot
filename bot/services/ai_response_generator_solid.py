"""
Генерация ответов AI - единственная ответственность
Принцип Single Responsibility + Dependency Inversion
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import google.generativeai as genai
from loguru import logger

from bot.config import AI_SYSTEM_PROMPT, settings


class IModerator(ABC):
    """Интерфейс для модерации (Dependency Inversion)"""
    
    @abstractmethod
    def moderate(self, text: str) -> tuple[bool, str]:
        pass


class IContextBuilder(ABC):
    """Интерфейс для построения контекста (Dependency Inversion)"""
    
    @abstractmethod
    def build(self, user_message: str, chat_history: List[Dict] = None, 
              user_age: Optional[int] = None) -> str:
        pass


class AIResponseGenerator:
    """Генерация ответов AI - единственная ответственность"""
    
    def __init__(self, moderator: IModerator, context_builder: IContextBuilder):
        """Dependency Injection - соблюдение DIP"""
        self.moderator = moderator
        self.context_builder = context_builder
        
        # Инициализация Gemini
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": settings.ai_temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": settings.ai_max_tokens,
            },
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
            ],
            system_instruction=AI_SYSTEM_PROMPT,
        )
        
        logger.info(f"✅ AI Response Generator инициализирован: {settings.gemini_model}")

    async def generate_response(self, user_message: str, chat_history: List[Dict] = None,
                               user_age: Optional[int] = None) -> str:
        """Генерация ответа AI"""
        try:
            # Модерация контента (делегирование ответственности)
            is_safe, reason = self.moderator.moderate(user_message)
            if not is_safe:
                return f"Извините, но я не могу обсуждать эту тему. {reason}"
            
            # Построение контекста (делегирование ответственности)
            context = self.context_builder.build(user_message, chat_history, user_age)
            
            # Генерация ответа (единственная ответственность этого класса)
            response = self.model.generate_content(context)
            
            if response and response.text:
                return response.text.strip()
            else:
                return "Извините, не смог сгенерировать ответ. Попробуйте переформулировать вопрос."
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации AI: {e}")
            return "Ой, что-то пошло не так. Попробуйте переформулировать вопрос."

    def get_model_info(self) -> Dict[str, str]:
        """Информация о модели"""
        return {
            "model": settings.gemini_model,
            "temperature": str(settings.ai_temperature),
            "max_tokens": str(settings.ai_max_tokens),
            "public_name": "PandaPalAI"
        }
