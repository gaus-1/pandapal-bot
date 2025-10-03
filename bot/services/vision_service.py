"""
Сервис обработки изображений с использованием Gemini Vision API
Анализирует изображения для образовательных задач и модерации
@module bot.services.vision_service
"""

import asyncio
import io
import base64
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import google.generativeai as genai
from loguru import logger
from aiogram.types import PhotoSize

from bot.config import settings
from bot.services.cache_service import cache_service
from bot.services.moderation_service import ContentModerationService


class ImageCategory(Enum):
    """Категории изображений"""
    EDUCATIONAL = "educational"
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    HISTORY = "history"
    ART = "art"
    TEXT = "text"
    DIAGRAM = "diagram"
    CHART = "chart"
    PHOTO = "photo"
    DRAWING = "drawing"
    INAPPROPRIATE = "inappropriate"
    UNKNOWN = "unknown"


class ImageSafetyLevel(Enum):
    """Уровни безопасности изображений"""
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    UNSAFE = "unsafe"


@dataclass
class ImageAnalysisResult:
    """Результат анализа изображения"""
    category: ImageCategory
    safety_level: ImageSafetyLevel
    description: str
    educational_content: Optional[str]
    subjects_detected: List[str]
    confidence: float
    moderation_flags: List[str]
    suggested_activities: List[str]


class VisionService:
    """
    Сервис обработки изображений с использованием Gemini Vision
    Анализирует изображения для образовательных целей и безопасности
    """
    
    def __init__(self):
        """Инициализация сервиса зрения"""
        self.api_key = settings.gemini_api_key
        self.model_name = settings.gemini_model
        
        # Настраиваем Gemini
        genai.configure(api_key=self.api_key)
        
        # Инициализируем модель с поддержкой изображений
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": 0.4,  # Более точный анализ изображений
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,
            },
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        )
        
        # Инициализируем сервис модерации
        self.moderation_service = ContentModerationService()
        
        logger.info("🖼️ Сервис обработки изображений инициализирован")
    
    async def analyze_image(
        self, 
        image_data: bytes, 
        user_message: Optional[str] = None,
        user_age: Optional[int] = None
    ) -> ImageAnalysisResult:
        """
        Анализировать изображение
        
        Args:
            image_data: Данные изображения в байтах
            user_message: Сопровождающий текст пользователя
            user_age: Возраст пользователя для адаптации ответа
            
        Returns:
            ImageAnalysisResult: Результат анализа изображения
        """
        try:
            # Проверяем кэш
            image_hash = await self._get_image_hash(image_data)
            cache_key = cache_service.generate_key("image_analysis", image_hash, user_message)
            
            cached_result = await cache_service.get(cache_key)
            if cached_result:
                logger.debug("💾 Результат анализа изображения получен из кэша")
                return ImageAnalysisResult(**cached_result)
            
            # Подготавливаем промпт для анализа
            analysis_prompt = self._build_analysis_prompt(user_message, user_age)
            
            # Конвертируем изображение для Gemini
            image_parts = self._prepare_image_for_gemini(image_data)
            
            # Выполняем анализ
            response = await self._analyze_with_gemini(image_parts, analysis_prompt)
            
            # Парсим результат
            result = self._parse_analysis_result(response)
            
            # Дополнительная модерация
            result = await self._apply_moderation(result, user_message)
            
            # Сохраняем в кэш
            await cache_service.set(cache_key, result.__dict__, ttl=3600)  # 1 час
            
            logger.info(f"🖼️ Изображение проанализировано: {result.category.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа изображения: {e}")
            return self._create_error_result(str(e))
    
    async def generate_educational_response(
        self, 
        analysis_result: ImageAnalysisResult,
        user_message: Optional[str] = None,
        user_age: Optional[int] = None
    ) -> str:
        """
        Генерировать образовательный ответ на основе анализа изображения
        
        Args:
            analysis_result: Результат анализа изображения
            user_message: Сообщение пользователя
            user_age: Возраст пользователя
            
        Returns:
            str: Образовательный ответ
        """
        try:
            if analysis_result.safety_level == ImageSafetyLevel.UNSAFE:
                return self.moderation_service.get_safe_response_alternative("inappropriate_image")
            
            # Строим образовательный промпт
            educational_prompt = self._build_educational_prompt(
                analysis_result, user_message, user_age
            )
            
            # Генерируем ответ
            response = await self._generate_educational_content(educational_prompt)
            
            # Адаптируем ответ под возраст
            adapted_response = self._adapt_response_for_age(response, user_age)
            
            logger.info(f"📚 Сгенерирован образовательный ответ для изображения: {analysis_result.category.value}")
            
            return adapted_response
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации образовательного ответа: {e}")
            return "😔 Извини, у меня возникли проблемы с анализом изображения. Попробуй ещё раз!"
    
    async def create_learning_task_from_image(
        self, 
        analysis_result: ImageAnalysisResult,
        user_age: Optional[int] = None,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создать образовательную задачу на основе изображения
        
        Args:
            analysis_result: Результат анализа изображения
            user_age: Возраст пользователя
            subject: Предмет (опционально)
            
        Returns:
            Dict[str, Any]: Образовательная задача
        """
        try:
            if analysis_result.safety_level != ImageSafetyLevel.SAFE:
                return {
                    "error": "Изображение не подходит для создания образовательных задач",
                    "reason": "Небезопасное содержание"
                }
            
            # Определяем предмет и сложность
            detected_subject = subject or self._detect_primary_subject(analysis_result)
            difficulty = self._calculate_difficulty(user_age, detected_subject)
            
            # Создаем задачу
            task = {
                "type": "image_analysis_task",
                "subject": detected_subject,
                "difficulty": difficulty,
                "description": analysis_result.description,
                "question": self._generate_task_question(analysis_result, detected_subject),
                "hints": self._generate_task_hints(analysis_result, detected_subject),
                "expected_answers": self._generate_expected_answers(analysis_result, detected_subject),
                "educational_value": analysis_result.educational_content,
                "age_appropriate": self._is_age_appropriate(analysis_result, user_age)
            }
            
            logger.info(f"📝 Создана образовательная задача: {detected_subject}")
            
            return task
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания образовательной задачи: {e}")
            return {
                "error": "Не удалось создать образовательную задачу",
                "reason": str(e)
            }
    
    def _build_analysis_prompt(self, user_message: Optional[str], user_age: Optional[int]) -> str:
        """Построить промпт для анализа изображения"""
        age_context = ""
        if user_age:
            age_context = f"Учитывай, что пользователю {user_age} лет. "
        
        message_context = ""
        if user_message:
            message_context = f"Пользователь написал: '{user_message}'. "
        
        return f"""
        {age_context}{message_context}
        
        Проанализируй это изображение для образовательного бота PandaPal, который помогает детям учиться.
        
        ОПИШИ ИЗОБРАЖЕНИЕ:
        - Что изображено на картинке?
        - Какие предметы, люди, животные или явления видны?
        - Есть ли текст, числа, формулы или схемы?
        
        ОПРЕДЕЛИ КАТЕГОРИЮ:
        - educational (образовательное содержание)
        - mathematics (математика, числа, графики)
        - science (наука, природа, эксперименты)
        - history (исторические события, артефакты)
        - art (искусство, рисунки, картины)
        - text (документы, книги, статьи)
        - diagram (схемы, диаграммы)
        - chart (графики, таблицы)
        - photo (обычные фотографии)
        - drawing (рисунки, эскизы)
        - inappropriate (неподходящий контент)
        - unknown (неопределенно)
        
        ОЦЕНИ БЕЗОПАСНОСТЬ:
        - safe (безопасно для детей)
        - suspicious (требует внимания)
        - unsafe (небезопасно)
        
        ВЫЯВИ ОБРАЗОВАТЕЛЬНЫЙ ПОТЕНЦИАЛ:
        - Какие предметы можно изучать по этому изображению?
        - Какие образовательные задачи можно создать?
        - Какой возраст подходит для изучения?
        
        ОТВЕТЬ В ФОРМАТЕ JSON:
        {{
            "category": "категория",
            "safety_level": "уровень_безопасности",
            "description": "подробное описание",
            "educational_content": "образовательная ценность",
            "subjects_detected": ["предмет1", "предмет2"],
            "confidence": 0.95,
            "moderation_flags": ["флаг1", "флаг2"],
            "suggested_activities": ["активность1", "активность2"]
        }}
        """
    
    def _prepare_image_for_gemini(self, image_data: bytes) -> Dict[str, Any]:
        """Подготовить изображение для отправки в Gemini"""
        # Конвертируем в base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Определяем MIME тип (предполагаем JPEG)
        mime_type = "image/jpeg"
        
        return {
            "mime_type": mime_type,
            "data": image_base64
        }
    
    async def _analyze_with_gemini(self, image_parts: Dict[str, Any], prompt: str) -> str:
        """Анализировать изображение с помощью Gemini"""
        try:
            # Создаем содержимое для модели
            content = [prompt, image_parts]
            
            # Генерируем ответ
            response = self.model.generate_content(content)
            
            return response.text
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа в Gemini: {e}")
            raise
    
    def _parse_analysis_result(self, response: str) -> ImageAnalysisResult:
        """Парсить результат анализа от Gemini"""
        try:
            # Извлекаем JSON из ответа
            import json
            import re
            
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
            else:
                # Если JSON не найден, создаем базовый результат
                data = {
                    "category": "unknown",
                    "safety_level": "safe",
                    "description": response[:200],
                    "educational_content": None,
                    "subjects_detected": [],
                    "confidence": 0.5,
                    "moderation_flags": [],
                    "suggested_activities": []
                }
            
            return ImageAnalysisResult(
                category=ImageCategory(data.get("category", "unknown")),
                safety_level=ImageSafetyLevel(data.get("safety_level", "safe")),
                description=data.get("description", ""),
                educational_content=data.get("educational_content"),
                subjects_detected=data.get("subjects_detected", []),
                confidence=float(data.get("confidence", 0.5)),
                moderation_flags=data.get("moderation_flags", []),
                suggested_activities=data.get("suggested_activities", [])
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга результата анализа: {e}")
            return self._create_error_result(f"Ошибка парсинга: {e}")
    
    async def _apply_moderation(self, result: ImageAnalysisResult, user_message: Optional[str]) -> ImageAnalysisResult:
        """Применить дополнительную модерацию"""
        try:
            # Проверяем описание изображения
            if result.description:
                is_safe, reason = self.moderation_service.is_safe_content(result.description)
                if not is_safe:
                    result.safety_level = ImageSafetyLevel.UNSAFE
                    result.moderation_flags.append(f"description_blocked: {reason}")
            
            # Проверяем сообщение пользователя
            if user_message:
                is_safe, reason = self.moderation_service.is_safe_content(user_message)
                if not is_safe:
                    result.safety_level = ImageSafetyLevel.UNSAFE
                    result.moderation_flags.append(f"message_blocked: {reason}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка модерации изображения: {e}")
            result.moderation_flags.append(f"moderation_error: {e}")
            return result
    
    def _build_educational_prompt(
        self, 
        analysis_result: ImageAnalysisResult,
        user_message: Optional[str],
        user_age: Optional[int]
    ) -> str:
        """Построить образовательный промпт"""
        age_context = f"Пользователю {user_age} лет. " if user_age else ""
        
        message_context = f"Пользователь спросил: '{user_message}'. " if user_message else ""
        
        subjects_text = ", ".join(analysis_result.subjects_detected) if analysis_result.subjects_detected else "общие знания"
        
        return f"""
        {age_context}{message_context}
        
        На основе анализа изображения создай образовательный ответ для ребёнка.
        
        ИЗОБРАЖЕНИЕ СОДЕРЖИТ:
        - Описание: {analysis_result.description}
        - Предметы: {subjects_text}
        - Образовательная ценность: {analysis_result.educational_content or 'не определена'}
        
        СОЗДАЙ ОТВЕТ, КОТОРЫЙ:
        1. Объясняет, что изображено на картинке
        2. Связывает это с учебными предметами
        3. Задаёт интересные вопросы для размышления
        4. Предлагает практические задания
        5. Использует простой и понятный язык для детей
        
        Будь дружелюбным, поощрительным и образовательным!
        """
    
    async def _generate_educational_content(self, prompt: str) -> str:
        """Генерировать образовательный контент"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации образовательного контента: {e}")
            return "😔 У меня возникли проблемы с анализом. Попробуй ещё раз!"
    
    def _adapt_response_for_age(self, response: str, user_age: Optional[int]) -> str:
        """Адаптировать ответ под возраст пользователя"""
        if not user_age:
            return response
        
        if user_age <= 8:
            # Упрощаем язык для младших школьников
            response = response.replace("следовательно", "поэтому")
            response = response.replace("необходимо", "нужно")
            response = response.replace("осуществить", "сделать")
        
        elif user_age >= 14:
            # Используем более сложные термины для старших школьников
            pass
        
        return response
    
    def _detect_primary_subject(self, analysis_result: ImageAnalysisResult) -> str:
        """Определить основной предмет по результату анализа"""
        if not analysis_result.subjects_detected:
            return "общие знания"
        
        # Маппинг категорий на предметы
        category_subject_map = {
            ImageCategory.MATHEMATICS: "математика",
            ImageCategory.SCIENCE: "биология",
            ImageCategory.HISTORY: "история",
            ImageCategory.ART: "изобразительное искусство",
            ImageCategory.TEXT: "русский язык",
            ImageCategory.DIAGRAM: "информатика",
            ImageCategory.CHART: "математика"
        }
        
        return category_subject_map.get(analysis_result.category, "общие знания")
    
    def _calculate_difficulty(self, user_age: Optional[int], subject: str) -> str:
        """Рассчитать сложность задачи"""
        if not user_age:
            return "средняя"
        
        if user_age <= 8:
            return "легкая"
        elif user_age <= 12:
            return "средняя"
        else:
            return "сложная"
    
    def _generate_task_question(self, analysis_result: ImageAnalysisResult, subject: str) -> str:
        """Сгенерировать вопрос для задачи"""
        base_questions = {
            "математика": "Что ты можешь сказать о числах на этом изображении?",
            "биология": "Какие живые организмы ты видишь на картинке?",
            "история": "Какой исторический период изображён?",
            "изобразительное искусство": "Какие цвета и формы ты замечаешь?",
            "русский язык": "Прочитай текст на изображении и перескажи его своими словами.",
            "информатика": "Опиши схему или диаграмму на картинке.",
            "общие знания": "Расскажи, что ты видишь на этом изображении."
        }
        
        return base_questions.get(subject, "Расскажи, что ты видишь на этом изображении.")
    
    def _generate_task_hints(self, analysis_result: ImageAnalysisResult, subject: str) -> List[str]:
        """Сгенерировать подсказки для задачи"""
        return [
            "Внимательно рассмотри все детали изображения",
            "Подумай о том, что ты уже знаешь по этой теме",
            "Опиши сначала общее, а потом детали"
        ]
    
    def _generate_expected_answers(self, analysis_result: ImageAnalysisResult, subject: str) -> List[str]:
        """Сгенерировать ожидаемые ответы"""
        return [
            analysis_result.description,
            "Описание основных элементов изображения",
            "Связь с изучаемым предметом"
        ]
    
    def _is_age_appropriate(self, analysis_result: ImageAnalysisResult, user_age: Optional[int]) -> bool:
        """Проверить, подходит ли изображение для возраста"""
        if analysis_result.safety_level != ImageSafetyLevel.SAFE:
            return False
        
        if not user_age:
            return True
        
        # Дополнительные проверки по возрасту можно добавить здесь
        return True
    
    async def _get_image_hash(self, image_data: bytes) -> str:
        """Получить хэш изображения для кэширования"""
        import hashlib
        return hashlib.md5(image_data).hexdigest()
    
    def _create_error_result(self, error_message: str) -> ImageAnalysisResult:
        """Создать результат с ошибкой"""
        return ImageAnalysisResult(
            category=ImageCategory.UNKNOWN,
            safety_level=ImageSafetyLevel.UNSAFE,
            description=f"Ошибка анализа: {error_message}",
            educational_content=None,
            subjects_detected=[],
            confidence=0.0,
            moderation_flags=[f"analysis_error: {error_message}"],
            suggested_activities=[]
        )
