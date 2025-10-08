"""
Модерация контента - единственная ответственность
Принцип Single Responsibility
"""

from typing import Tuple
from loguru import logger

from bot.config import FORBIDDEN_PATTERNS
from bot.services.ai_response_generator_solid import IModerator


class ContentModerator(IModerator):
    """Модерация контента - единственная ответственность"""
    
    def moderate(self, text: str) -> Tuple[bool, str]:
        """Проверка контента на безопасность"""
        text_lower = text.lower()
        
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.lower() in text_lower:
                logger.warning(f"🚫 Запрещенный контент: {pattern}")
                return False, f"Запрещенная тема: {pattern}"
        
        return True, "Контент безопасен"
