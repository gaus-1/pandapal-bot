"""
Сервис интеграции образовательной базы знаний с AI.

Этот модуль объединяет веб-парсинг образовательных сайтов с AI для
предоставления более точных и актуальных ответов по школьным предметам.
Теперь с поддержкой Wikipedia API для получения проверенных данных.
"""

import json
import os
import re
from datetime import datetime, timedelta
from urllib.parse import quote

import httpx
from loguru import logger

from bot.config import FORBIDDEN_PATTERNS
from bot.services.cache_service import cache_service
from bot.services.rag import (
    ContextCompressor,
    QueryExpander,
    ResultReranker,
    SemanticCache,
    VectorSearchService,
)
from bot.services.web_scraper import EducationalContent, WebScraperService

# Языки Википедии (совпадают с SUPPORTED_LANGUAGES в translate_service)
WIKIPEDIA_LANGUAGES = frozenset({"ru", "en", "de", "fr", "es"})

# Query rewriting для RAG: короткое сообщение-продолжение диалога
RAG_QUERY_SHORT_MESSAGE_MAX_LEN = 40
RAG_QUERY_TOPIC_MAX_CHARS = 300
RAG_QUERY_CONTINUATION_PHRASES = frozenset(
    {
        "а ещё",
        "ещё?",
        "а почему",
        "а это",
        "а можно",
        "и что",
        "а что с этим",
        "почему так",
        "а зачем",
        "а как",
        "а где",
    }
)


def _normalize_wikipedia_lang(language_code: str | None) -> str:
    """Нормализация кода языка для Wikipedia API (ru, en, de, fr, es)."""
    if not language_code or not str(language_code).strip():
        return "ru"
    code = str(language_code).strip().lower()[:2]
    return code if code in WIKIPEDIA_LANGUAGES else "ru"


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
        self.auto_update_enabled = os.getenv("KNOWLEDGE_AUTO_UPDATE", "false").lower() == "true"

        # Wikipedia API (БЕЗ ключа - открытый API); URL по языку в методах
        self.wikipedia_timeout = httpx.Timeout(10.0, connect=5.0)

        # RAG компоненты
        self.query_expander = QueryExpander()
        self.reranker = ResultReranker()
        self.semantic_cache = SemanticCache(ttl_hours=24)
        self.vector_search = VectorSearchService()

        # Запрещенные паттерны для детей (ТОЛЬКО опасный контент, НЕ образовательный)
        # "война", "смерть" и т.д. - это учебные темы истории, их НЕ блокируем
        self.forbidden_topics = frozenset(
            {
                # Инструкции по созданию опасных вещей
                "как сделать бомбу",
                "как изготовить взрывчатку",
                "рецепт наркотик",
                # Призывы к насилию и суициду
                "способы самоубийства",
                "как покончить с собой",
                "призыв к насилию",
                # Экстремизм и терроризм
                "вступить в игил",
                "террористическая организация вербует",
                # Взрослый контент
                "порнограф",
                "эротическ",
            }
        )

        # Глобальные FORBIDDEN_PATTERNS (>5 символов, чтобы не ловить false positives)
        self._critical_forbidden_patterns = frozenset(p for p in FORBIDDEN_PATTERNS if len(p) > 5)

        logger.info(
            f"📚 KnowledgeService инициализирован (RAG: ON, авто-обновление: {'ВКЛ' if self.auto_update_enabled else 'ВЫКЛ'})"
        )

    @staticmethod
    def _wikipedia_api_url(lang: str) -> str:
        """URL API Википедии для языка (ru, en, de, fr, es)."""
        return f"https://{lang}.wikipedia.org/w/api.php"

    @staticmethod
    def _wikipedia_wiki_base_url(lang: str) -> str:
        """Базовый URL статей Википедии для языка."""
        return f"https://{lang}.wikipedia.org"

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

    @staticmethod
    def build_rag_query(user_message: str, chat_history: list[dict] | None = None) -> str:
        """
        Строит поисковый запрос для RAG: при коротком «продолжении» дополняет контекстом последнего ответа.

        Если истории нет или нет ответов assistant — возвращает user_message.
        Иначе при коротком сообщении (≤40 символов) с маркерами продолжения («а ещё», «а почему» и т.п.)
        возвращает фрагмент последнего ответа + сообщение; иначе — только user_message.
        """
        if not chat_history:
            return user_message.strip()
        last_assistant_text = None
        for msg in reversed(chat_history):
            if msg.get("role") == "assistant":
                last_assistant_text = (msg.get("text") or "").strip()
                break
        if not last_assistant_text:
            return user_message.strip()
        msg_stripped = user_message.strip()
        if len(msg_stripped) > RAG_QUERY_SHORT_MESSAGE_MAX_LEN:
            return msg_stripped
        msg_lower = msg_stripped.lower()
        if not any(phrase in msg_lower for phrase in RAG_QUERY_CONTINUATION_PHRASES):
            return msg_stripped
        topic = last_assistant_text.split("\n")[0].strip()
        if len(topic) > RAG_QUERY_TOPIC_MAX_CHARS:
            cut = topic[:RAG_QUERY_TOPIC_MAX_CHARS]
            last_space = cut.rfind(" ")
            topic = (cut[:last_space] if last_space > 0 else cut) + "…"
        return f"{topic} {msg_stripped}"

    async def enhanced_search(
        self,
        user_question: str,
        user_age: int | None = None,
        top_k: int = 3,
        use_wikipedia: bool = True,
        language_code: str | None = None,
    ) -> list[EducationalContent]:
        """
        Улучшенный поиск с RAG компонентами.
        При пустой базе и use_wikipedia=True подтягивает контекст из Wikipedia.

        Args:
            user_question: Вопрос пользователя
            user_age: Возраст для адаптации
            top_k: Количество результатов
            use_wikipedia: Подтянуть Wikipedia при отсутствии результатов из базы
            language_code: Код языка для Wikipedia (ru, en, de, fr, es); по умолчанию ru

        Returns:
            Топ-K переранжированных результатов
        """
        cached_result = await self.semantic_cache.get(user_question)
        if cached_result:
            logger.debug(f"📚 Semantic cache hit: {user_question[:50]}")
            return cached_result

        # 1. Векторный поиск (semantic)
        vector_results = await self.vector_search.search(user_question, top_k=5)

        # 2. Keyword поиск
        expanded_query = self.query_expander.expand(user_question)
        logger.debug(f"📚 Expanded query: {expanded_query}")
        query_variations = self.query_expander.generate_variations(user_question)
        keyword_results = []
        for variation in query_variations:
            results = await self.get_helpful_content(variation, user_age)
            keyword_results.extend(results)

        all_results = vector_results + keyword_results
        unique_results = self._deduplicate_results(all_results)

        # 3. Wikipedia fallback; при получении — индексируем для будущего семантического поиска
        if not unique_results and use_wikipedia:
            wiki_content = await self.get_wikipedia_educational(
                user_question, user_age, language_code=language_code
            )
            if wiki_content:
                unique_results = [wiki_content]
                await self.vector_search.index_content(wiki_content)

        ranked_results = self.reranker.rerank(user_question, unique_results, user_age, top_k=top_k)

        if ranked_results:
            await self.semantic_cache.set(user_question, ranked_results)

        return ranked_results

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

                # Инвалидация semantic cache при обновлении базы: старый кэш может содержать устаревшие результаты
                try:
                    self.semantic_cache.clear()
                    logger.debug("🗑️ Semantic cache очищен после обновления базы знаний")
                except Exception as cache_err:
                    logger.debug(f"Semantic cache clear: {cache_err}")

                logger.info(
                    f"✅ База знаний обновлена: {len(all_materials)} материалов по {len(self.knowledge_base)} предметам"
                )

                # Индексация в pgvector для семантического поиска
                indexed = 0
                for material in all_materials:
                    try:
                        if await self.vector_search.index_content(material):
                            indexed += 1
                    except Exception as idx_err:
                        logger.warning(
                            f"⚠️ Не удалось проиндексировать материал «{material.title[:50]}»: {idx_err}"
                        )
                if indexed:
                    logger.info(f"📚 Проиндексировано в векторы: {indexed} материалов")

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

    @staticmethod
    def _paragraphize_snippet(text: str, max_chars: int = 1000) -> str:
        """Разбить сплошной текст на абзацы (по 1–2 предложения), чтобы модель не копировала стену текста."""
        if not text or len(text) > max_chars:
            text = (text or "")[:max_chars]
        if "\n\n" in text:
            return text.strip()
        sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) <= 1:
            return text.strip()
        parts = []
        buf = []
        for sent in sentences:
            buf.append(sent)
            if len(buf) >= 2:
                parts.append(" ".join(buf))
                buf = []
        if buf:
            parts.append(" ".join(buf))
        result = "\n\n".join(parts)
        return result[:max_chars] if len(result) > max_chars else result

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

        content_limit = 1000
        for i, material in enumerate(materials[:3], 1):  # Берем топ-3 материала
            formatted_content += f"\n{i}. {material.title}\n"
            formatted_content += f"   Предмет: {material.subject}\n"
            raw = material.content[:content_limit]
            content_snippet = self._paragraphize_snippet(raw) if raw else ""
            suffix = "..." if len(material.content) > content_limit else ""
            formatted_content += f"   Содержание: {content_snippet}{suffix}\n"
            formatted_content += f"   Источник: {material.source_url}\n"

        formatted_content += (
            "\n\nИспользуй эту информацию для более точного и актуального ответа. "
            "Не упоминай Wikipedia и источники в ответе."
        )

        return formatted_content

    def format_and_compress_knowledge_for_ai(
        self,
        materials: list[EducationalContent],
        question: str,
        max_sentences: int = 15,
    ) -> str:
        """
        Форматировать материалы и сжать контекст для промпта (единая точка для stream и generate_response).
        """
        formatted = self.format_knowledge_for_ai(materials)
        if not formatted:
            return ""
        return ContextCompressor().compress(
            context=formatted, question=question, max_sentences=max_sentences
        )

    async def _wikipedia_search_title(self, topic: str, language_code: str = "ru") -> str | None:
        """
        Найти заголовок страницы по поисковому запросу (fallback при отсутствии точного titles).
        """
        lang = _normalize_wikipedia_lang(language_code)
        api_url = self._wikipedia_api_url(lang)
        try:
            params = {
                "action": "query",
                "list": "search",
                "srsearch": topic,
                "srlimit": 1,
                "format": "json",
            }
            headers = {
                "User-Agent": "PandaPal/1.0 (Educational Bot; contact@pandapal.ru)",
                "Accept": "application/json",
            }
            async with httpx.AsyncClient(timeout=self.wikipedia_timeout, headers=headers) as client:
                response = await client.get(api_url, params=params)
                response.raise_for_status()
                data = response.json()
            search = data.get("query", {}).get("search", [])
            if search:
                return search[0].get("title")
        except Exception as e:
            logger.debug(f"Wikipedia search fallback для '{topic}': {e}")
        return None

    async def get_wikipedia_summary(
        self,
        topic: str,
        user_age: int | None = None,
        max_length: int = 500,
        language_code: str | None = None,
    ) -> tuple[str, str] | None:
        """
        Получить краткое описание темы из проверенного источника.
        БЕЗ ключа - открытый API, работает из России.
        При отсутствии страницы по точному titles выполняется поиск (list=search).

        Args:
            topic: Название темы для поиска.
            user_age: Возраст пользователя для адаптации контента.
            max_length: Максимальная длина ответа (символов).
            language_code: Код языка Википедии (ru, en, de, fr, es).

        Returns:
            (extract, title) или None при ошибке.
        """
        if not topic or not topic.strip():
            return None

        lang = _normalize_wikipedia_lang(language_code)
        api_url = self._wikipedia_api_url(lang)
        topic_normalized = topic.strip().lower()
        cache_key = f"wikipedia:{lang}:{topic_normalized}:{user_age or 'all'}"

        cached = await cache_service.get(cache_key)
        if cached:
            try:
                obj = json.loads(cached)
                logger.debug(f"📚 Кэш попадание для темы: {topic}")
                return (obj["e"], obj["t"])
            except (json.JSONDecodeError, KeyError):
                pass

        headers = {
            "User-Agent": "PandaPal/1.0 (Educational Bot; contact@pandapal.ru)",
            "Accept": "application/json",
        }

        try:
            params = {
                "action": "query",
                "prop": "extracts",
                "exintro": "1",
                "explaintext": "1",
                "titles": topic,
                "format": "json",
            }
            async with httpx.AsyncClient(timeout=self.wikipedia_timeout, headers=headers) as client:
                response = await client.get(api_url, params=params)
                response.raise_for_status()
                data = response.json()

            pages = data.get("query", {}).get("pages", {})
            if not pages:
                logger.debug(f"📚 Страница не найдена для '{topic}'")
                return None

            page = list(pages.values())[0]
            title = page.get("title", topic)

            if page.get("missing") or page.get("invalid"):
                found_title = await self._wikipedia_search_title(topic, language_code=lang)
                if found_title:
                    async with httpx.AsyncClient(
                        timeout=self.wikipedia_timeout, headers=headers
                    ) as client:
                        resp = await client.get(
                            api_url,
                            params={
                                "action": "query",
                                "prop": "extracts",
                                "exintro": "1",
                                "explaintext": "1",
                                "titles": found_title,
                                "format": "json",
                            },
                        )
                        resp.raise_for_status()
                        data = resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    if not pages:
                        return None
                    page = list(pages.values())[0]
                    title = page.get("title", found_title)
                else:
                    logger.debug(f"📚 Страница отсутствует и поиск не дал результата для '{topic}'")
                    return None

            extract = page.get("extract", "").strip()
            if not extract:
                found_title = await self._wikipedia_search_title(topic, language_code=lang)
                if found_title and found_title != title:
                    async with httpx.AsyncClient(
                        timeout=self.wikipedia_timeout, headers=headers
                    ) as client:
                        resp = await client.get(
                            api_url,
                            params={
                                "action": "query",
                                "prop": "extracts",
                                "exintro": "1",
                                "explaintext": "1",
                                "titles": found_title,
                                "format": "json",
                            },
                        )
                        resp.raise_for_status()
                        data = resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    if pages:
                        page = list(pages.values())[0]
                        title = page.get("title", found_title)
                        extract = page.get("extract", "").strip()
            if not extract:
                logger.debug(f"📚 Пустой контент для '{topic}'")
                return None

            if self._contains_forbidden_content(extract):
                logger.warning(f"⚠️ Запрещенный контент обнаружен для '{topic}'")
                return None

            extract = self._adapt_content_for_children(extract, user_age)
            if len(extract) > max_length:
                sentences = re.split(r"([.!?]\s+)", extract[: max_length + 100])
                extract = "".join(sentences[:-2]) if len(sentences) > 2 else extract[:max_length]
                extract = extract.strip() + "..."

            await cache_service.set(cache_key, json.dumps({"e": extract, "t": title}), ttl=86400)
            logger.debug(
                f"✅ Получены данные для '{topic}' ({len(extract)} символов, возраст: {user_age or 'all'})"
            )
            return (extract, title)

        except httpx.TimeoutException:
            logger.warning(f"⚠️ Таймаут при получении данных для '{topic}'")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"⚠️ HTTP ошибка {e.response.status_code} для '{topic}'")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных для '{topic}': {e}")
            return None

    def _contains_forbidden_content(self, text: str) -> bool:  # noqa: ARG002
        """
        Проверить, содержит ли текст запрещенный контент.
        Дополнительный safety-фильтр для внешнего контента в детском приложении.
        Проверяет и по локальным forbidden_topics, и по общим FORBIDDEN_PATTERNS.
        """
        if not text or not text.strip():
            return False
        text_lower = text.lower()
        # Проверка по локальным паттернам (опасный контент: бомба, суицид, порно и т.д.)
        if any(pattern in text_lower for pattern in self.forbidden_topics):
            return True
        # Проверка по глобальным запрещённым паттернам (расширенный набор >5 символов)
        return any(pattern in text_lower for pattern in self._critical_forbidden_patterns)

    def _adapt_content_for_children(self, text: str, user_age: int | None = None) -> str:
        """
        Адаптировать контент для детей: упрощение, удаление сложных терминов.

        Args:
            text: Исходный текст.
            user_age: Возраст пользователя.

        Returns:
            str: Адаптированный текст.
        """
        # Удаляем технические пометки из текста
        text = re.sub(r"\[примечание \d+\]", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\[источник не указан \d+ дней?\]", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\[когда\?\]", "", text, flags=re.IGNORECASE)

        # Упрощаем сложные конструкции для младших классов
        if user_age and user_age <= 10:
            # Заменяем сложные слова на более простые
            replacements = {
                r"\bосуществляется\b": "происходит",
                r"\bявляется\b": "это",
                r"\bпредставляет собой\b": "это",
                r"\bхарактеризуется\b": "отличается",
                r"\bосуществлять\b": "делать",
            }
            for pattern, replacement in replacements.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Удаляем лишние пробелы
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        return text

    def _extract_topic_from_question(self, question: str) -> str | None:
        """
        Извлечь тему из вопроса пользователя для поиска проверенных данных.

        Args:
            question: Вопрос пользователя.

        Returns:
            str: Извлеченная тема или None.
        """
        question_lower = question.lower().strip()

        # Паттерны для извлечения темы
        patterns = [
            r"список\s+(.+?)(?:\?|\.|$)",
            r"таблиц[аеы]?\s+(?:значений?\s+)?(.+?)(?:\?|\.|$)",
            r"все\s+значения\s+(.+?)(?:\?|\.|$)",
            r"что такое\s+(.+?)(?:\?|\.|$)",
            r"кто такой\s+(.+?)(?:\?|\.|$)",
            r"кто такая\s+(.+?)(?:\?|\.|$)",
            r"расскажи про\s+(.+?)(?:\?|\.|$)",
            r"расскажи о\s+(.+?)(?:\?|\.|$)",
            r"объясни\s+(.+?)(?:\?|\.|$)",
            r"что значит\s+(.+?)(?:\?|\.|$)",
            r"что означает\s+(.+?)(?:\?|\.|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, question_lower)
            if match:
                topic = match.group(1).strip()
                # Убираем лишние слова
                topic = re.sub(r"\s+(это|такое|такой|такая)\s*$", "", topic, flags=re.IGNORECASE)
                if len(topic) > 2 and len(topic) < 100:  # Разумные границы
                    return topic

        # Если паттерны не сработали, берем первые слова вопроса
        words = question.split()
        if len(words) >= 2:
            # Берем первые 2-4 слова
            topic = " ".join(words[: min(4, len(words))])
            # Убираем вопросительные слова
            topic = re.sub(
                r"^(что|кто|как|где|когда|почему|зачем)\s+", "", topic, flags=re.IGNORECASE
            )
            if len(topic) > 2 and len(topic) < 100:
                return topic

        return None

    async def get_wikipedia_context_for_question(
        self,
        question: str,
        user_age: int | None = None,
        language_code: str | None = None,
    ) -> str | None:
        """
        Получить проверенный контекст для вопроса пользователя.

        Args:
            question: Вопрос пользователя.
            user_age: Возраст пользователя.
            language_code: Код языка Википедии (ru, en, de, fr, es).

        Returns:
            str: Проверенный контекст или None.
        """
        topic = self._extract_topic_from_question(question)
        if not topic:
            return None
        result = await self.get_wikipedia_summary(
            topic, user_age, max_length=1200, language_code=language_code
        )
        return result[0] if result else None

    async def get_wikipedia_educational(
        self,
        question: str,
        user_age: int | None = None,
        language_code: str | None = None,
    ) -> EducationalContent | None:
        """
        Получить Wikipedia-контент в виде EducationalContent для RAG (когда база пуста).
        """
        topic = self._extract_topic_from_question(question)
        if not topic:
            return None
        lang = _normalize_wikipedia_lang(language_code)
        result = await self.get_wikipedia_summary(
            topic, user_age, max_length=1200, language_code=language_code
        )
        if not result:
            return None
        extract, title = result
        url_title = quote(title.replace(" ", "_"), safe="")
        base_url = self._wikipedia_wiki_base_url(lang)
        return EducationalContent(
            title=title,
            content=extract,
            subject="общее",
            difficulty="средний",
            source_url=f"{base_url}/wiki/{url_title}",
            extracted_at=datetime.now(),
            tags=["wikipedia"],
        )

    def _deduplicate_results(self, results: list) -> list:
        """Удалить дубликаты из результатов."""
        seen_urls = set()
        unique = []

        for result in results:
            url = getattr(result, "source_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(result)
            elif not url:
                # Если нет URL, проверяем по title
                title = getattr(result, "title", "")
                if title and title not in [getattr(r, "title", "") for r in unique]:
                    unique.append(result)

        return unique


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
