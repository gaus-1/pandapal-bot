"""
Сервис интеграции образовательной базы знаний с AI.

Этот модуль объединяет веб-парсинг образовательных сайтов с AI для
предоставления более точных и актуальных ответов по школьным предметам.
"""

from datetime import datetime, timedelta

from loguru import logger

from bot.services.web_scraper import EducationalContent, WebScraperService


class KnowledgeService:
    """
    Сервис для управления образовательной базой знаний.

    Объединяет парсинг веб-сайтов с AI для предоставления
    актуальной информации по всем школьным предметам.
    """

    def __init__(self):
        """Инициализация сервиса знаний."""
        self.knowledge_base: dict[str, list[EducationalContent]] = {}
        self.last_update: datetime | None = None
        self.update_interval = timedelta(days=7)  # Обновляем раз в неделю
        self.auto_update_enabled = False  # Отключено для быстрых ответов

        logger.info("📚 KnowledgeService инициализирован (авто-обновление: ВЫКЛ)")

    async def get_knowledge_for_subject(
        self, subject: str, query: str = ""
    ) -> list[EducationalContent]:
        """
        Получить знания по конкретному предмету.

        Args:
            subject: Название предмета.
            query: Поисковый запрос для фильтрации.

        Returns:
            List[EducationalContent]: Список релевантных материалов.
        """
        # Проверяем, нужно ли обновить базу знаний
        if self._should_update_knowledge_base():
            await self.update_knowledge_base()

        # Получаем материалы по предмету
        subject_materials = self.knowledge_base.get(subject, [])

        # Если есть поисковый запрос, фильтруем результаты
        if query:
            query_lower = query.lower()
            subject_materials = [
                material
                for material in subject_materials
                if query_lower in material.title.lower() or query_lower in material.content.lower()
            ]

        return subject_materials

    async def get_helpful_content(
        self,
        user_question: str,
        user_age: int | None = None,  # noqa: ARG002
    ) -> list[EducationalContent]:
        """
        Найти полезный контент для ответа на вопрос пользователя.

        Args:
            user_question: Вопрос пользователя.
            user_age: Возраст пользователя для адаптации.

        Returns:
            List[EducationalContent]: Список релевантных материалов.
        """
        # Обновляем базу знаний если нужно
        if self._should_update_knowledge_base():
            await self.update_knowledge_base()

        relevant_materials = []
        question_lower = user_question.lower()

        # Ищем релевантные материалы во всех предметах
        for subject, materials in self.knowledge_base.items():
            for material in materials:
                # Проверяем релевантность по заголовку и содержанию
                if (
                    question_lower in material.title.lower()
                    or question_lower in material.content.lower()
                    or self._is_question_related_to_subject(question_lower, subject)
                ):
                    relevant_materials.append(material)

        # Сортируем по релевантности (простейший алгоритм)
        relevant_materials.sort(key=lambda x: len(x.content), reverse=True)

        return relevant_materials[:5]  # Возвращаем топ-5 релевантных материалов

    def _is_question_related_to_subject(self, question: str, subject: str) -> bool:
        """
        Проверить, связан ли вопрос с предметом.

        Args:
            question: Вопрос пользователя в нижнем регистре.
            subject: Название предмета.

        Returns:
            bool: True если вопрос связан с предметом.
        """
        # Ключевые слова для каждого предмета
        subject_keywords = {
            "matematika": [
                "математика",
                "число",
                "решить",
                "задача",
                "уравнение",
                "формула",
                "считать",
                "плюс",
                "минус",
                "умножить",
                "делить",
                "дробь",
                "процент",
                "геометрия",
                "алгебра",
            ],
            "russkiy-yazyk": [
                "русский",
                "язык",
                "слово",
                "предложение",
                "грамматика",
                "орфография",
                "пунктуация",
                "часть речи",
                "существительное",
                "прилагательное",
                "глагол",
                "написать",
                "сочинение",
                "изложение",
            ],
            "literatura": [
                "литература",
                "книга",
                "писатель",
                "поэт",
                "стихотворение",
                "рассказ",
                "роман",
                "произведение",
                "автор",
                "герой",
                "сюжет",
                "тема",
                "идея",
            ],
            "istoriya": [
                "история",
                "исторический",
                "война",
                "революция",
                "царь",
                "император",
                "древний",
                "средние века",
                "современность",
                "дата",
                "событие",
                "персона",
            ],
            "geografiya": [
                "география",
                "страна",
                "город",
                "столица",
                "материк",
                "океан",
                "река",
                "гора",
                "климат",
                "население",
                "карта",
                "координаты",
            ],
            "biologiya": [
                "биология",
                "животное",
                "растение",
                "клетка",
                "орган",
                "система",
                "размножение",
                "эволюция",
                "экосистема",
                "природа",
                "человек",
                "анатомия",
            ],
            "fizika": [
                "физика",
                "сила",
                "энергия",
                "скорость",
                "масса",
                "температура",
                "давление",
                "электричество",
                "магнетизм",
                "свет",
                "звук",
                "механика",
            ],
            "khimiya": [
                "химия",
                "химический",
                "элемент",
                "реакция",
                "вещество",
                "молекула",
                "атом",
                "периодическая",
                "таблица",
                "менделеева",
                "менделеев",
                "периодическая таблица",
                "таблица менделеева",
                "кислота",
                "щелочь",
                "соль",
            ],
            "informatika": [
                "информатика",
                "компьютер",
                "программа",
                "алгоритм",
                "код",
                "программирование",
                "интернет",
                "сайт",
                "данные",
                "файл",
                "система",
            ],
        }

        keywords = subject_keywords.get(subject, [])
        return any(keyword in question for keyword in keywords)

    def _should_update_knowledge_base(self) -> bool:
        """Проверить, нужно ли обновить базу знаний."""
        # Если авто-обновление отключено, возвращаем False
        if not self.auto_update_enabled:
            return False

        if not self.last_update:
            return True

        time_diff = datetime.now() - self.last_update
        return bool(time_diff > self.update_interval)

    async def update_knowledge_base(self):
        """Обновить базу знаний из веб-источников."""
        try:
            logger.info("🔄 Обновление базы знаний...")

            async with WebScraperService() as scraper:
                # Собираем материалы с nsportal.ru
                nsportal_materials = await scraper.scrape_nsportal_tasks(100)

                # Собираем материалы с school203.spb.ru
                school203_materials = await scraper.scrape_school203_content(50)

                # Объединяем все материалы
                all_materials = nsportal_materials + school203_materials

                # Группируем по предметам
                self.knowledge_base = {}
                for material in all_materials:
                    subject = material.subject
                    if subject not in self.knowledge_base:
                        self.knowledge_base[subject] = []
                    self.knowledge_base[subject].append(material)

                self.last_update = datetime.now()

                logger.info(
                    f"✅ База знаний обновлена: {len(all_materials)} материалов по {len(self.knowledge_base)} предметам"
                )

        except Exception as e:
            logger.error(f"❌ Ошибка обновления базы знаний: {e}")

    def get_knowledge_stats(self) -> dict[str, int]:
        """
        Получить статистику базы знаний.

        Returns:
            Dict[str, int]: Статистика по предметам.
        """
        stats = {}
        for subject, materials in self.knowledge_base.items():
            stats[subject] = len(materials)

        return stats

    def format_knowledge_for_ai(self, materials: list[EducationalContent]) -> str:
        """
        Форматировать материалы для передачи в AI.

        Args:
            materials: Список образовательных материалов.

        Returns:
            str: Отформатированная строка для AI.
        """
        if not materials:
            return ""

        formatted_content = "\n\n📚 РЕЛЕВАНТНЫЕ МАТЕРИАЛЫ ИЗ ОБРАЗОВАТЕЛЬНЫХ ИСТОЧНИКОВ:\n"

        for i, material in enumerate(materials[:3], 1):  # Берем топ-3 материала
            formatted_content += f"\n{i}. {material.title}\n"
            formatted_content += f"   Предмет: {material.subject}\n"
            formatted_content += f"   Содержание: {material.content[:300]}...\n"
            formatted_content += f"   Источник: {material.source_url}\n"

        formatted_content += (
            "\n\nИспользуй эту информацию для более точного и актуального ответа! 🎯"
        )

        return formatted_content


# Глобальный экземпляр сервиса
_knowledge_service = None


def get_knowledge_service() -> KnowledgeService:
    """
    Получить экземпляр сервиса знаний.

    Returns:
        KnowledgeService: Экземпляр сервиса.
    """
    global _knowledge_service

    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()

    return _knowledge_service
