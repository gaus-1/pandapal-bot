"""
Сервис для парсинга образовательных сайтов и извлечения учебных материалов.

Этот модуль реализует функциональность для автоматического сбора информации
с образовательных сайтов, включая задачи, новости и учебные материалы.

Безопасность (OWASP A10 - SSRF):
- Все внешние URL валидируются через SSRFProtection
- Разрешены только whitelisted домены
- Блокируются внутренние IP и localhost
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from bot.security import SSRFProtection, validate_url_safety


@dataclass
class EducationalContent:
    """
    Структура для хранения образовательного контента.

    Attributes:
        title (str): Название материала или задачи.
        content (str): Текстовое содержимое материала.
        subject (str): Учебный предмет (математика, русский язык и т.д.).
        difficulty (str): Уровень сложности (легкий, средний, сложный).
        source_url (str): URL источника материала.
        extracted_at (datetime): Время извлечения контента.
        tags (List[str]): Теги для классификации и поиска.
    """

    title: str
    content: str
    subject: str
    difficulty: str
    source_url: str
    extracted_at: datetime
    tags: list[str]


@dataclass
class NewsItem:
    """
    Структура для хранения новостных статей.

    Attributes:
        title (str): Заголовок новости.
        content (str): Текст новости.
        url (str): Ссылка на полную версию.
        published_date (Optional[datetime]): Дата публикации (если доступна).
        source (str): Источник новости (nsportal.ru, school203.spb.ru и т.д.).
    """

    title: str
    content: str
    url: str
    published_date: datetime | None
    source: str


class WebScraperService:
    """
    Сервис для парсинга образовательных сайтов.

    Поддерживает извлечение задач, новостей и учебных материалов
    с nsportal.ru и school203.spb.ru.
    """

    def __init__(self):
        """Инициализация сервиса парсинга."""
        self.session: aiohttp.ClientSession | None = None
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        # Настройки для сайтов
        self.nsportal_config = {
            "base_url": "https://nsportal.ru",
            "library_url": "https://nsportal.ru/shkola",
            "news_url": "https://nsportal.ru/novosti",
            "subjects": [
                "matematika",
                "russkiy-yazyk",
                "literatura",
                "istoriya",
                "geografiya",
                "biologiya",
                "fizika",
                "khimiya",
                "informatika",
            ],
        }

        self.school203_config = {
            "base_url": "https://school203.spb.ru",
            "sections": [
                "uchebnaya-deyatelnost",
                "vospitatelnaya-rabota",
                "dopolnitelnoe-obrazovanie",
                "metodicheskaya-rabota",
            ],
        }

        logger.info("🌐 WebScraperService инициализирован")

    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход."""
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # noqa: ARG002
        """Асинхронный контекстный менеджер - выход."""
        await self.close_session()

    async def start_session(self):
        """Запустить HTTP сессию."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout, headers={"User-Agent": self.user_agent}
            )

    async def close_session(self):
        """Закрыть HTTP сессию."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _safe_get(self, url: str) -> aiohttp.ClientResponse | None:
        """
        Безопасный HTTP GET запрос с SSRF защитой (OWASP A10).

        Args:
            url: URL для запроса

        Returns:
            Response объект или None если URL небезопасен
        """
        # Валидация URL перед запросом
        if not validate_url_safety(url):
            logger.warning(f"🚫 SSRF: заблокирован небезопасный URL: {url}")
            return None

        # Дополнительная проверка через SSRFProtection
        if not SSRFProtection.validate_external_request(url, "GET"):
            logger.warning(f"🚫 SSRF: запрос к {url} заблокирован политикой безопасности")
            return None

        try:
            return await self.session.get(url)
        except Exception as e:
            logger.error(f"❌ Ошибка HTTP запроса к {url}: {e}")
            return None

    async def scrape_nsportal_tasks(self, limit: int = 50) -> list[EducationalContent]:
        """
        Парсить задачи с nsportal.ru.

        Args:
            limit: Максимальное количество задач для извлечения.

        Returns:
            List[EducationalContent]: Список найденных задач.
        """
        tasks = []

        try:
            # Парсим библиотеку по предметам
            for subject in self.nsportal_config["subjects"]:
                subject_url = f"{self.nsportal_config['library_url']}/{subject}"
                subject_tasks = await self._scrape_nsportal_subject(
                    subject_url, subject, limit // len(self.nsportal_config["subjects"])
                )
                tasks.extend(subject_tasks)

                # Небольшая задержка между запросами
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга nsportal.ru: {e}")

        return tasks[:limit]

    async def _scrape_nsportal_subject(
        self, url: str, subject: str, limit: int
    ) -> list[EducationalContent]:
        """Парсить задачи по конкретному предмету с nsportal.ru."""
        tasks = []

        try:
            response = await self._safe_get(url)
            if response and response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Ищем ссылки на материалы
                material_links = soup.find_all("a", href=True)[:limit]

                for link in material_links:
                    try:
                        link_href = str(link.get("href", ""))
                        if link_href:
                            material_url = urljoin(url, link_href)
                            task = await self._extract_nsportal_material(material_url, subject)
                            if task:
                                tasks.append(task)
                    except Exception as e:
                        logger.debug(f"Ошибка извлечения материала: {e}")
                        continue

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга предмета {subject}: {e}")

        return tasks

    async def _extract_nsportal_material(self, url: str, subject: str) -> EducationalContent | None:
        """Извлечь материал с nsportal.ru."""
        try:
            response = await self._safe_get(url)
            if response and response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Извлекаем заголовок
                title_elem = soup.find("h1") or soup.find("title")
                title = title_elem.get_text().strip() if title_elem else "Материал без названия"

                # Извлекаем контент
                content_elem = soup.find("div", class_="content") or soup.find("main")
                if not content_elem:
                    content_elem = soup.find("body")

                content = content_elem.get_text().strip() if content_elem else ""

                # Очищаем контент
                content = re.sub(r"\s+", " ", content)
                content = content[:2000]  # Ограничиваем длину

                if len(content) > 100:  # Только содержательные материалы
                    return EducationalContent(
                        title=title,
                        content=content,
                        subject=subject,
                        difficulty="средняя",
                        source_url=url,
                        extracted_at=datetime.now(),
                        tags=[subject, "nsportal.ru"],
                    )

        except Exception as e:
            logger.debug(f"Ошибка извлечения материала {url}: {e}")

        return None

    async def scrape_school203_content(self, limit: int = 30) -> list[EducationalContent]:
        """
        Парсить контент с school203.spb.ru.

        Args:
            limit: Максимальное количество материалов.

        Returns:
            List[EducationalContent]: Список найденных материалов.
        """
        materials = []

        try:
            # Парсим основные разделы
            for section in self.school203_config["sections"]:
                section_url = f"{self.school203_config['base_url']}/{section}"
                section_materials = await self._scrape_school203_section(
                    section_url, section, limit // len(self.school203_config["sections"])
                )
                materials.extend(section_materials)

                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга school203.spb.ru: {e}")

        return materials[:limit]

    async def _scrape_school203_section(
        self, url: str, section: str, limit: int
    ) -> list[EducationalContent]:
        """Парсить раздел school203.spb.ru."""
        materials = []

        try:
            response = await self._safe_get(url)
            if response and response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Ищем статьи и материалы
                articles = soup.find_all(
                    ["article", "div"], class_=re.compile(r"(article|post|content)")
                )[:limit]

                for article in articles:
                    try:
                        material = await self._extract_school203_material(article, section)
                        if material:
                            materials.append(material)
                    except Exception as e:
                        logger.debug(f"Ошибка извлечения статьи: {e}")
                        continue

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга раздела {section}: {e}")

        return materials

    async def _extract_school203_material(
        self, article_elem, section: str
    ) -> EducationalContent | None:
        """Извлечь материал из статьи school203.spb.ru."""
        try:
            # Извлекаем заголовок
            title_elem = article_elem.find(["h1", "h2", "h3", "h4"])
            title = title_elem.get_text().strip() if title_elem else "Материал без названия"

            # Извлекаем контент
            content_elem = article_elem.find("div", class_=re.compile(r"(content|text|body)"))
            if not content_elem:
                content_elem = article_elem

            content = content_elem.get_text().strip()
            content = re.sub(r"\s+", " ", content)
            content = content[:2000]

            if len(content) > 50:
                return EducationalContent(
                    title=title,
                    content=content,
                    subject=section,
                    difficulty="средняя",
                    source_url="",  # URL не всегда доступен
                    extracted_at=datetime.now(),
                    tags=[section, "school203.spb.ru"],
                )

        except Exception as e:
            logger.debug(f"Ошибка извлечения материала: {e}")

        return None

    async def scrape_news(self, days_back: int = 7) -> list[NewsItem]:
        """
        Парсить новости с образовательных сайтов.

        Args:
            days_back: Количество дней назад для поиска новостей.

        Returns:
            List[NewsItem]: Список найденных новостей.
        """
        news = []

        try:
            # Парсим новости с nsportal.ru
            nsportal_news = await self._scrape_nsportal_news(days_back)
            news.extend(nsportal_news)

            # Парсим новости с school203.spb.ru
            school203_news = await self._scrape_school203_news(days_back)
            news.extend(school203_news)

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга новостей: {e}")

        return news

    async def _scrape_nsportal_news(self, days_back: int) -> list[NewsItem]:  # noqa: ARG002
        """Парсить новости с nsportal.ru."""
        news = []

        try:
            news_url = self.nsportal_config["news_url"]
            response = await self._safe_get(news_url)
            if response and response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Ищем новости
                news_items = soup.find_all(
                    ["article", "div"], class_=re.compile(r"(news|article|post)")
                )[:20]

                for item in news_items:
                    try:
                        news_item = await self._extract_news_item(item, "nsportal.ru")
                        if news_item:
                            news.append(news_item)
                    except Exception as e:
                        logger.debug(f"Ошибка извлечения новости: {e}")
                        continue

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга новостей nsportal.ru: {e}")

        return news

    async def _scrape_school203_news(self, days_back: int) -> list[NewsItem]:  # noqa: ARG002
        """Парсить новости с school203.spb.ru."""
        news = []

        try:
            # Ищем раздел новостей
            news_url = f"{self.school203_config['base_url']}/novosti"
            response = await self._safe_get(news_url)
            if response and response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Ищем новости
                news_items = soup.find_all(
                    ["article", "div"], class_=re.compile(r"(news|article|post)")
                )[:15]

                for item in news_items:
                    try:
                        news_item = await self._extract_news_item(item, "school203.spb.ru")
                        if news_item:
                            news.append(news_item)
                    except Exception as e:
                        logger.debug(f"Ошибка извлечения новости: {e}")
                        continue

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга новостей school203.spb.ru: {e}")

        return news

    async def _extract_news_item(self, item_elem, source: str) -> NewsItem | None:
        """Извлечь новость из элемента."""
        try:
            # Извлекаем заголовок
            title_elem = item_elem.find(["h1", "h2", "h3", "h4", "a"])
            title = title_elem.get_text().strip() if title_elem else "Новость без названия"

            # Извлекаем контент
            content_elem = item_elem.find(
                ["p", "div"], class_=re.compile(r"(content|text|summary)")
            )
            if not content_elem:
                content_elem = item_elem

            content = content_elem.get_text().strip()
            content = re.sub(r"\s+", " ", content)
            content = content[:500]

            # Извлекаем URL
            url_elem = item_elem.find("a", href=True)
            url = (
                urljoin(
                    (
                        self.nsportal_config["base_url"]
                        if "nsportal" in source
                        else self.school203_config["base_url"]
                    ),
                    url_elem["href"],
                )
                if url_elem
                else ""
            )

            if len(content) > 20:
                return NewsItem(
                    title=title,
                    content=content,
                    url=url,
                    published_date=datetime.now(),  # Точную дату сложно извлечь
                    source=source,
                )

        except Exception as e:
            logger.debug(f"Ошибка извлечения новости: {e}")

        return None

    async def get_educational_knowledge_base(self) -> dict[str, list[EducationalContent]]:
        """
        Получить базу знаний по всем предметам.

        Returns:
            Dict[str, List[EducationalContent]]: Словарь с материалами по предметам.
        """
        knowledge_base: dict[str, list[EducationalContent]] = {}

        try:
            # Собираем материалы с nsportal.ru
            nsportal_materials = await self.scrape_nsportal_tasks(100)

            # Собираем материалы с school203.spb.ru
            school203_materials = await self.scrape_school203_content(50)

            # Объединяем все материалы
            all_materials = nsportal_materials + school203_materials

            # Группируем по предметам
            for material in all_materials:
                subject = material.subject
                if subject not in knowledge_base:
                    knowledge_base[subject] = []
                knowledge_base[subject].append(material)

            logger.info(
                f"📚 База знаний собрана: {len(all_materials)} материалов по {len(knowledge_base)} предметам"
            )

        except Exception as e:
            logger.error(f"❌ Ошибка создания базы знаний: {e}")

        return knowledge_base


# Глобальный экземпляр сервиса
_web_scraper = None


async def get_web_scraper() -> WebScraperService:
    """
    Получить экземпляр сервиса парсинга веб-сайтов.

    Returns:
        WebScraperService: Экземпляр сервиса.
    """
    global _web_scraper

    if _web_scraper is None:
        _web_scraper = WebScraperService()
        await _web_scraper.start_session()

    return _web_scraper
