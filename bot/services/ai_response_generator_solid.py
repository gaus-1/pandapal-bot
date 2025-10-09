"""
Генератор ответов AI с соблюдением принципов SOLID.

Этот модуль реализует архитектуру для генерации ответов AI с использованием
принципов SOLID (Single Responsibility, Open/Closed, Liskov Substitution,
Interface Segregation, Dependency Inversion).

Основные компоненты:
- Интерфейсы для модерации и построения контекста (ISP, DIP)
- Реализация генератора ответов с интеграцией TokenRotator (SRP)
- Автоматическое переключение токенов при ошибках квоты (OCP)
- Поддержка истории чата и адаптации под возраст пользователя
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import google.generativeai as genai
from loguru import logger

from bot.config import AI_SYSTEM_PROMPT, settings
from bot.services.token_rotator import get_token_rotator


class IModerator(ABC):
    """
    Интерфейс для модерации контента.

    Следует принципу Interface Segregation (ISP) - содержит только методы,
    необходимые для модерации, без лишних зависимостей.
    """

    @abstractmethod
    def moderate(self, text: str) -> tuple[bool, str]:
        """
        Проверить текст на соответствие правилам модерации.

        Args:
            text (str): Текст для проверки.

        Returns:
            tuple[bool, str]: Кортеж (is_safe, reason), где:
                - is_safe (bool): True если текст безопасен, False если нарушает правила
                - reason (str): Причина отклонения (если is_safe=False)
        """
        pass


class IContextBuilder(ABC):
    """
    Интерфейс для построения контекста для AI.

    Следует принципу Interface Segregation (ISP) - содержит только методы
    для построения контекста, необходимые для генерации ответов.
    """

    @abstractmethod
    def build(
        self, user_message: str, chat_history: List[Dict] = None, user_age: Optional[int] = None
    ) -> str:
        """
        Построить контекст для генерации ответа AI.

        Args:
            user_message (str): Текущее сообщение пользователя.
            chat_history (List[Dict], optional): История предыдущих сообщений.
            user_age (Optional[int]): Возраст пользователя для адаптации ответа.

        Returns:
            str: Сформированный контекст для передачи в AI модель.
        """
        pass


class AIResponseGenerator:
    """
    Генератор ответов AI с соблюдением принципа Single Responsibility.

    Единственная ответственность этого класса - генерация ответов AI.
    Все остальные функции (модерация, построение контекста, ротация токенов)
    делегируются соответствующим сервисам через Dependency Injection.
    """

    def __init__(self, moderator: IModerator, context_builder: IContextBuilder):
        """
        Инициализация генератора ответов с внедрением зависимостей.

        Следует принципу Dependency Inversion (DIP) - зависит от абстракций
        (интерфейсов), а не от конкретных реализаций.

        Args:
            moderator (IModerator): Сервис модерации контента.
            context_builder (IContextBuilder): Сервис построения контекста.
        """
        self.moderator = moderator
        self.context_builder = context_builder

        # Инициализация Gemini с ротатором токенов
        self.token_rotator = get_token_rotator()
        self._configure_gemini()

    def _configure_gemini(self) -> None:
        """
        Настройка Gemini AI модели с текущим токеном.

        Конфигурирует Google Generative AI с использованием текущего активного
        токена из ротатора, настраивает параметры генерации и настройки безопасности.

        Raises:
            ValueError: Если нет доступных API токенов.
        """
        token = self.token_rotator.get_current_token()
        if not token:
            raise ValueError("Нет доступных API токенов")

        genai.configure(api_key=token)
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

    async def generate_response(
        self, user_message: str, chat_history: List[Dict] = None, user_age: Optional[int] = None
    ) -> str:
        """
        Генерировать ответ AI на сообщение пользователя.

        Основной метод класса, реализующий принцип Single Responsibility.
        Координирует работу модерации, построения контекста и генерации ответа,
        с автоматическим переключением токенов при ошибках квоты.

        Args:
            user_message (str): Сообщение пользователя для обработки.
            chat_history (List[Dict], optional): История предыдущих сообщений для контекста.
            user_age (Optional[int]): Возраст пользователя для адаптации ответа.

        Returns:
            str: Сгенерированный ответ AI или сообщение об ошибке.
        """
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
            error_msg = str(e)
            logger.error(f"❌ Ошибка генерации AI: {e}")

            # Проверяем, не исчерпана ли квота
            quota_indicators = ["quota", "429", "exceeded", "limit", "retry in"]
            if any(indicator in error_msg.lower() for indicator in quota_indicators):
                logger.warning("⚠️ Квота токена исчерпана, переключаемся на следующий")
                current_token = self.token_rotator.get_current_token()
                if current_token:
                    self.token_rotator.mark_token_failed(current_token, "quota_exceeded")

                    # Пробуем с новым токеном
                    try:
                        self._configure_gemini()
                        response = self.model.generate_content(context)
                        if response and response.text:
                            return response.text.strip()
                    except Exception as retry_error:
                        logger.error(f"❌ Ошибка при повторной попытке: {retry_error}")

            return "Ой, что-то пошло не так. Попробуйте переформулировать вопрос."

    def get_model_info(self) -> Dict[str, str]:
        """
        Получить информацию о текущей модели AI.

        Returns:
            Dict[str, str]: Словарь с информацией о модели:
                - model: Название модели Gemini
                - temperature: Температура генерации
                - max_tokens: Максимальное количество токенов
                - public_name: Публичное название для пользователей
        """
        return {
            "model": settings.gemini_model,
            "temperature": str(settings.ai_temperature),
            "max_tokens": str(settings.ai_max_tokens),
            "public_name": "PandaPalAI",
        }
