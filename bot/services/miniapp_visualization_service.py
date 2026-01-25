"""
Сервис для обработки визуализаций в Mini App.

Отвечает за:
- Детекцию запросов на визуализации (таблицы, графики)
- Генерацию визуализаций (таблицы умножения, графики функций, комбинированные)
- Постобработку текста (удаление дубликатов, обрезка до коротких объяснений)
"""

import re

from loguru import logger

from bot.services.miniapp_intent_service import VisualizationIntent
from bot.services.visualization_service import get_visualization_service


class MiniappVisualizationService:
    """Сервис для обработки визуализаций в Mini App."""

    def __init__(self):
        """Инициализация сервиса."""
        self.viz_service = get_visualization_service()

    def detect_visualization_request(
        self, user_message: str, intent: VisualizationIntent
    ) -> tuple[bytes | None, int | None, bool, bool, str | None]:
        """
        Детектирует запрос на визуализацию.

        Args:
            user_message: Сообщение пользователя
            intent: Результат парсинга IntentService

        Returns:
            tuple: (specific_visualization_image, multiplication_number, general_table_request, general_graph_request, visualization_type)
        """
        user_msg_lower = user_message.lower()

        # Расширенные паттерны для таблиц умножения (конкретные числа)
        multiplication_patterns = [
            r"табл[иы]ц[аеы]?\s*умножени[яе]\s*на\s*(\d+)",
            r"табл[иы]ц[аеы]?\s*умножени[яе]\s+(\d+)",
            r"умножени[яе]\s+на\s*(\d+)",
            r"умнож[а-я]*\s+(\d+)",
        ]

        # Функция проверки контекста
        def has_specific_context(text: str) -> bool:
            """Проверяет, есть ли в запросе специфичные слова."""
            specific_keywords = [
                r"глагол",
                r"падеж",
                r"алфавит",
                r"букв",
                r"звук",
                r"орфограф",
                r"пунктуац",
                r"морфемн",
                r"стил\s+реч",
                r"сопряжени[яе]",
                r"спряжени[яе]",
                r"времен[а]?\s+год",
                r"месяц",
                r"дн[ия]?\s+недел",
                r"часов[ые]?\s+пояс",
                r"страны?",
                r"хронологи",
                r"ветв[и]?\s+власт",
                r"систем[ы]?\s+счислени",
                r"природн[ые]?\s+зон",
                r"растворимост",
                r"валентност",
                r"менделеева",
                r"периодическая",
                r"констант",
                r"плотност",
                r"теплоемкост",
                r"сопротивлени",
                r"неправильн",
                r"времен[а]?\s+(?:английск|англ)",
                r"график\s+(?:пути|путь|скорост|движени[яе])",
                r"график\s+(?:функци[яи]|y\s*=|x\s*\*\*|sin|cos|tan|log|sqrt)",
                r"график\s+(?:закон|ома|гука|парабол|линейн)",
                r"график\s+(?:температур|плавлени|кристаллизац)",
                r"график\s+(?:изотерм|изобар|изохор)",
                r"график\s+(?:переменн[ый]?\s+ток|ac\s+current)",
            ]
            return any(re.search(keyword, text) for keyword in specific_keywords)

        # Общие паттерны для запросов на таблицы (без числа)
        general_table_patterns = [
            r"состав[ьи]\s+табл[иы]ц[аеы]?",
            r"пришли\s+табл[иы]ц[аеы]?",
            r"покажи\s+табл[иы]ц[аеы]?",
            r"сделай\s+табл[иы]ц[аеы]?",
            r"нарисуй\s+табл[иы]ц[аеы]?",
            r"построй\s+табл[иы]ц[аеы]?",
            r"выведи\s+табл[иы]ц[аеы]?",
            r"дай\s+табл[иы]ц[аеы]?",
            r"нужн[аы]?\s+табл[иы]ц[аеы]?",
            r"табл[иы]ц[аеы]?\s*(?:пришли|покажи|сделай|нарисуй|состав[ьи]|построй|дай)",
            r"покажи\s+умножени[яе]",
            r"табл[иы]ц[аеы]?\s*умножени[яе](?:\s+на\s+все)?",
            r"полную\s+табл[иы]ц[аеы]?\s*умножени[яе]",
            r"хочу\s+табл[иы]ц[аеы]?",
        ]

        # Расширенные паттерны для графиков
        general_graph_patterns = [
            r"состав[ьи]\s+график",
            r"пришли\s+график",
            r"покажи\s+график",
            r"сделай\s+график",
            r"нарисуй\s+график",
            r"построй\s+график",
            r"выведи\s+график",
            r"дай\s+график",
            r"нужен\s+график",
            r"хочу\s+график",
            r"график\s+(?:покажи|нарисуй|построй|сделай|выведи)",
        ]

        # Проверяем специфичные таблицы через detect_visualization_request
        specific_visualization_image = None
        visualization_type = None
        try:
            specific_visualization_image, visualization_type = (
                self.viz_service.detect_visualization_request(user_message)
            )

            # Если IntentService определил несколько таблиц умножения, игнорируем одиночную
            # специфичную визуализацию и будем генерировать комбинированную картинку
            try:
                multiple_table_intent = (
                    intent.kind == "table"
                    and isinstance(intent.items, list)
                    and len([n for n in intent.items if isinstance(n, int)]) > 1
                )
            except Exception:
                multiple_table_intent = False

            if multiple_table_intent and specific_visualization_image is not None:
                logger.info(
                    f"🔄 Stream: Игнорируем специфичную визуализацию для множественных таблиц: {intent.items}"
                )
                specific_visualization_image = None

            if specific_visualization_image:
                logger.info(f"📊 Детектирована специфичная визуализация: '{user_message[:50]}'")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при детекции специфичной визуализации: {e}")

        # Проверяем конкретные таблицы умножения (с числом) - только если специфичная визуализация не найдена
        multiplication_number = None
        if not specific_visualization_image:
            for pattern in multiplication_patterns:
                multiplication_match = re.search(pattern, user_msg_lower)
                if multiplication_match:
                    try:
                        multiplication_number = int(multiplication_match.group(1))
                        if 1 <= multiplication_number <= 10:
                            break
                    except (ValueError, IndexError):
                        continue

        # Проверяем общие запросы на таблицы (без числа)
        general_table_request = None
        if not specific_visualization_image and not multiplication_number:
            for pattern in general_table_patterns:
                if re.search(pattern, user_msg_lower):
                    general_table_request = True
                    logger.info(
                        f"📊 Детектирован общий запрос на таблицу: '{user_message[:50]}', pattern: {pattern}"
                    )
                    break

        # Проверяем общие запросы на графики
        general_graph_request = None
        for pattern in general_graph_patterns:
            if re.search(pattern, user_msg_lower):
                general_graph_request = True
                logger.info(
                    f"📈 Детектирован общий запрос на график: '{user_message[:50]}', pattern: {pattern}"
                )
                break

        return (
            specific_visualization_image,
            multiplication_number,
            general_table_request,
            general_graph_request,
            visualization_type,  # Тип визуализации для пояснений
        )

    def generate_visualization(
        self,
        user_message: str,
        full_response: str,
        intent: VisualizationIntent,
        specific_visualization_image: bytes | None,
        multiplication_number: int | None,
        general_table_request: bool | None,
        general_graph_request: bool | None,
    ) -> str | None:
        """
        Генерирует визуализацию на основе запроса.

        Args:
            user_message: Сообщение пользователя
            full_response: Полный ответ AI
            intent: Результат парсинга IntentService
            specific_visualization_image: Специфичная визуализация (если найдена)
            multiplication_number: Число для таблицы умножения (если найдено)
            general_table_request: Общий запрос на таблицу
            general_graph_request: Общий запрос на график

        Returns:
            str: Base64 строка изображения или None
        """
        user_msg_lower = user_message.lower()
        visualization_image_base64 = None

        try:
            # КРИТИЧНО: Если найдена специфичная визуализация - используем её
            if specific_visualization_image:
                try:
                    visualization_image_base64 = self.viz_service.image_to_base64(
                        specific_visualization_image
                    )
                    logger.info(
                        f"📊 Stream: Использована специфичная визуализация для '{user_message[:50]}' "
                        f"(размер base64: {len(visualization_image_base64) if visualization_image_base64 else 0})"
                    )
                except Exception as e:
                    logger.error(
                        f"❌ Stream: Ошибка конвертации специфичной визуализации в base64: {e}"
                    )
                    visualization_image_base64 = None

            # Если не нашли в запросе, проверяем ответ AI
            elif not multiplication_number:
                multiplication_patterns = [
                    r"табл[иы]ц[аеы]?\s*умножени[яе]\s*на\s*(\d+)",
                    r"табл[иы]ц[аеы]?\s*умножени[яе]\s+(\d+)",
                    r"умножени[яе]\s+на\s*(\d+)",
                    r"умнож[а-я]*\s+(\d+)",
                ]
                for pattern in multiplication_patterns:
                    multiplication_match = re.search(pattern, full_response.lower())
                    if multiplication_match:
                        try:
                            multiplication_number = int(multiplication_match.group(1))
                            if 1 <= multiplication_number <= 10:
                                break
                        except (ValueError, IndexError):
                            continue

            # Генерируем таблицу умножения используя IntentService
            if intent.kind == "table" and intent.items:
                multiplication_numbers = [
                    item for item in intent.items if isinstance(item, int) and 1 <= item <= 10
                ]
                if multiplication_numbers:
                    if len(multiplication_numbers) > 1:
                        # Несколько таблиц в одной картинке
                        visualization_image = (
                            self.viz_service.generate_multiple_multiplication_tables(
                                multiplication_numbers
                            )
                        )
                        logger.info(
                            f"📊 Stream: Сгенерированы таблицы умножения на {multiplication_numbers}"
                        )
                    else:
                        # Одна таблица
                        visualization_image = self.viz_service.generate_multiplication_table_image(
                            multiplication_numbers[0]
                        )
                        logger.info(
                            f"📊 Stream: Сгенерирована таблица умножения на {multiplication_numbers[0]}"
                        )

                    if visualization_image:
                        visualization_image_base64 = self.viz_service.image_to_base64(
                            visualization_image
                        )

            # Старая логика для обратной совместимости (если intent не сработал)
            elif multiplication_number:
                visualization_image = self.viz_service.generate_multiplication_table_image(
                    multiplication_number
                )
                if visualization_image:
                    visualization_image_base64 = self.viz_service.image_to_base64(
                        visualization_image
                    )
                    logger.info(
                        f"📊 Stream: Сгенерирована таблица умножения на {multiplication_number}"
                    )

            # ВАЖНО: Генерируем общую таблицу только если нет специфичной визуализации
            elif (
                general_table_request
                and not visualization_image_base64
                and not specific_visualization_image
            ):
                # Генерируем полную таблицу умножения (1-10)
                visualization_image = self.viz_service.generate_full_multiplication_table()
                if visualization_image:
                    visualization_image_base64 = self.viz_service.image_to_base64(
                        visualization_image
                    )
                    logger.info("📊 Stream: Сгенерирована полная таблица умножения")

            # Определяем, нужен ли график функции (расширенный паттерн)
            graph_match = None
            if general_graph_request and not visualization_image_base64:
                # Общий запрос на график - анализируем контекст для определения типа
                graph_patterns = [
                    r"график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                    r"нарисуй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                    r"построй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                    r"покажи\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                    r"(?:синусоид|sin|косинус|cos|тангенс|tan|экспонент|exp|логарифм|log|парабол|порабол|парабола|порабола)",
                ]
                for pattern in graph_patterns:
                    graph_match = re.search(pattern, user_msg_lower)
                    if graph_match:
                        break

                # Если не нашли в запросе, проверяем в ответе AI
                if not graph_match:
                    for pattern in graph_patterns:
                        graph_match = re.search(pattern, full_response.lower())
                        if graph_match:
                            break

            # Если есть график в запросе (не общий запрос)
            if not general_graph_request and not visualization_image_base64:
                graph_patterns = [
                    r"график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                    r"нарисуй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                    r"построй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                    r"покажи\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                    r"(?:синусоид|sin|косинус|cos|тангенс|tan|экспонент|exp|логарифм|log|парабол|порабол|парабола|порабола)",
                ]
                for pattern in graph_patterns:
                    graph_match = re.search(pattern, user_msg_lower)
                    if graph_match:
                        break

            # Генерируем комбинированную визуализацию для смешанных запросов (таблица + график)
            if intent.kind == "both":
                # Извлекаем число для таблицы
                table_numbers_attr = getattr(intent, "table_numbers", [])
                table_num = None
                if table_numbers_attr:
                    table_num = table_numbers_attr[0] if table_numbers_attr else None
                elif intent.items:
                    table_num = next(
                        (
                            item
                            for item in intent.items
                            if isinstance(item, int) and 1 <= item <= 10
                        ),
                        None,
                    )
                elif multiplication_number:
                    table_num = multiplication_number

                # Извлекаем выражение для графика
                graph_functions_attr = getattr(intent, "graph_functions", None)
                graph_expr = None
                if graph_functions_attr:
                    graph_expr = graph_functions_attr[0] if graph_functions_attr else None
                elif intent.items:
                    graph_expr = next(
                        (item for item in intent.items if isinstance(item, str)),
                        None,
                    )

                # Генерируем комбинированную картинку
                if table_num and graph_expr:
                    visualization_image = self.viz_service.generate_combined_table_and_graph(
                        table_num, graph_expr
                    )
                    if visualization_image:
                        visualization_image_base64 = self.viz_service.image_to_base64(
                            visualization_image
                        )
                        logger.info(
                            f"📊📈 Stream: Сгенерирована комбинированная визуализация: "
                            f"таблица на {table_num} + график {graph_expr}"
                        )
                else:
                    logger.warning(
                        f"⚠️ Stream: Не удалось извлечь данные для комбинированной визуализации: "
                        f"table_num={table_num}, graph_expr={graph_expr}"
                    )

            # Генерируем графики используя IntentService (только для kind="graph")
            elif intent.kind == "graph" and intent.items:
                graph_expressions = [item for item in intent.items if isinstance(item, str)]
                if graph_expressions:
                    if len(graph_expressions) > 1:
                        # Несколько графиков в одной картинке
                        visualization_image = self.viz_service.generate_multiple_function_graphs(
                            graph_expressions
                        )
                        logger.info(
                            f"📈 Stream: Сгенерированы графики функций: {graph_expressions}"
                        )
                    else:
                        # Один график
                        visualization_image = self.viz_service.generate_function_graph(
                            graph_expressions[0]
                        )
                        logger.info(
                            f"📈 Stream: Сгенерирован график функции: {graph_expressions[0]}"
                        )

                    if visualization_image:
                        visualization_image_base64 = self.viz_service.image_to_base64(
                            visualization_image
                        )

            # Старая логика для обратной совместимости
            elif (general_graph_request or graph_match) and not visualization_image_base64:
                # Если это запрос на синусоиду/косинус/параболу и т.д. без конкретной формулы
                logger.info(
                    f"🔍 Stream: Проверка типа графика: general_graph={general_graph_request}, "
                    f"graph_match={bool(graph_match)}, user_msg='{user_message[:50]}'"
                )
                # ИСПРАВЛЕНО: Добавлен "синус" в паттерн для поиска слова "синуса"
                sin_match = re.search(r"(?:синусоид|sin|синус)", user_msg_lower)
                logger.info(
                    f"🔍 Stream: Проверка синуса: sin_match={bool(sin_match)}, "
                    f"general_graph={general_graph_request}, graph_match={bool(graph_match)}"
                )
                if sin_match or (general_graph_request and not graph_match):
                    # Генерируем стандартный график синуса
                    logger.info("🔍 Stream: Вход в блок генерации графика синуса")
                    visualization_image = self.viz_service.generate_function_graph("sin(x)")
                    logger.info(
                        f"🔍 Stream: generate_function_graph вернул: {type(visualization_image)}, "
                        f"size={len(visualization_image) if visualization_image else 0}"
                    )
                    if visualization_image:
                        visualization_image_base64 = self.viz_service.image_to_base64(
                            visualization_image
                        )
                        logger.info(
                            f"📈 Stream: Сгенерирован график синусоиды, base64 size={len(visualization_image_base64)}"
                        )
                    else:
                        logger.warning("⚠️ Stream: generate_function_graph вернул None для sin(x)")
                elif re.search(r"(?:косинус|cos)", user_msg_lower):
                    visualization_image = self.viz_service.generate_function_graph("cos(x)")
                    if visualization_image:
                        visualization_image_base64 = self.viz_service.image_to_base64(
                            visualization_image
                        )
                        logger.info("📈 Stream: Сгенерирован график косинуса")
                elif re.search(r"(?:тангенс|tan|тангенсоид)", user_msg_lower):
                    visualization_image = self.viz_service.generate_function_graph("tan(x)")
                    if visualization_image:
                        visualization_image_base64 = self.viz_service.image_to_base64(
                            visualization_image
                        )
                        logger.info("📈 Stream: Сгенерирован график тангенса")
                elif re.search(r"(?:парабол|порабол|парабола|порабола)", user_msg_lower):
                    # Парабола y = x^2
                    visualization_image = self.viz_service.generate_function_graph("x**2")
                    if visualization_image:
                        visualization_image_base64 = self.viz_service.image_to_base64(
                            visualization_image
                        )
                        logger.info("📈 Stream: Сгенерирован график параболы")
                else:
                    expression = graph_match.group(1).strip() if graph_match.groups() else ""
                    # Безопасные выражения для графиков (поддерживаем x^2, x**2, x², x³)
                    if expression:
                        # ИСПРАВЛЕНО: Нормализуем выражение ПЕРЕД проверкой регулярным выражением
                        # Заменяем ², ³, ^ на ** для Python
                        expression = (
                            expression.replace("²", "**2").replace("³", "**3").replace("^", "**")
                        )
                        # Проверяем безопасность выражения (после нормализации)
                        if re.match(r"^[x\s+\-*/().\d\s]+$", expression):
                            visualization_image = self.viz_service.generate_function_graph(
                                expression
                            )
                            if visualization_image:
                                visualization_image_base64 = self.viz_service.image_to_base64(
                                    visualization_image
                                )
                                logger.info(f"📈 Stream: Сгенерирован график функции: {expression}")
                            else:
                                logger.warning(
                                    f"⚠️ Stream: Не удалось сгенерировать график для выражения: {expression}"
                                )
                        else:
                            logger.warning(
                                f"⚠️ Stream: Выражение не прошло проверку безопасности: {expression}"
                            )

        except Exception as e:
            logger.debug(f"⚠️ Stream: Ошибка генерации визуализации: {e}")

        return visualization_image_base64

    def postprocess_text_for_visualization(
        self,
        full_response: str,
        intent: VisualizationIntent,
        visualization_image_base64: str | None,
        multiplication_number: int | None,
    ) -> str:
        """
        Постобрабатывает текст ответа для визуализаций.

        Args:
            full_response: Полный ответ AI
            intent: Результат парсинга IntentService
            visualization_image_base64: Base64 строка изображения (если есть)
            multiplication_number: Число для таблицы умножения (если найдено)

        Returns:
            str: Обработанный текст ответа
        """
        if not visualization_image_base64:
            return full_response

        # Удаляем ВСЕ упоминания про автоматическую генерацию в ЛЮБОЙ формулировке
        patterns_to_remove = [
            # Общие паттерны автоматической генерации
            r"(?:систем[аеы]?\s+)?автоматически\s+сгенериру[ею]т?\s+[^.!?\n]*",
            r"покажу\s+(?:график|таблиц[ау]|карт[ау]|диаграмм[ау]|схем[ау]).*?систем[аеы]?\s+автоматически",
            r"автоматически\s+создан[аоы]?\s+[^.!?\n]*",
            r"создан[аоы]?\s+автоматически[^.!?\n]*",
            r"генерируется\s+автоматически[^.!?\n]*",
            r"автоматическая\s+генерация[^.!?\n]*",
            r"сгенерирован[аоы]?\s+автоматически[^.!?\n]*",
            # Паттерны в скобках
            r"\[Сгенерирован[аоы]?\s+[^\]]+\]",
            r"\(Сгенерирован[аоы]?\s+[^\)]+\)",
            r"\[Создан[аоы]?\s+автоматически[^\]]*\]",
            r"\(Создан[аоы]?\s+автоматически[^\)]*\)",
            # Паттерны "Это/Эта/Этот ... был создан/сгенерирован"
            r"Эт[аои][тй]?\s+(?:карт[ау]|график|таблиц[ау]|диаграмм[ау]|схем[ау]|изображени[ея]?)\s+был[аоы]?\s+(?:создан[аоы]?|сгенерирован[аоы]?)[^.!?\n]*",
            # Паттерны владельца/системы
            r"владельцем\s+сайт[аа]?[^.!?\n]*",
            r"на\s+основе\s+данных[^.!?\n]*",
            r"создан[аоы]?\s+(?:автоматически\s+)?владельцем[^.!?\n]*",
            r"сгенерирован[аоы]?\s+(?:автоматически\s+)?владельцем[^.!?\n]*",
            # Специфичные для карт
            r"карт[ау]\s+(?:был[аоы]?\s+)?создан[аоы]?\s+автоматически[^.!?\n]*",
            r"карт[ау]\s+(?:был[аоы]?\s+)?сгенерирован[аоы]?\s+автоматически[^.!?\n]*",
            # Английские паттерны
            r"(?:auto)?matically\s+generated[^.!?\n]*",
            r"generated\s+(?:auto)?matically[^.!?\n]*",
            r"this\s+(?:map|chart|graph|table|image)\s+was\s+(?:auto)?matically[^.!?\n]*",
            r"created\s+(?:auto)?matically[^.!?\n]*",
            # Паттерны "система покажет/создаст/добавит"
            r"систем[аеы]?\s+(?:покажет|создаст|добавит|сгенерирует)[^.!?\n]*",
            r"(?:будет\s+)?показан[аоы]?\s+автоматически[^.!?\n]*",
            r"(?:будет\s+)?добавлен[аоы]?\s+автоматически[^.!?\n]*",
            # Примечания и сноски
            r"\*\s*(?:Примечание|Note)[^.!?\n]*автоматически[^.!?\n]*",
            r"(?:Изображение|Карта|График|Таблица)\s+выше[^.!?\n]*автоматически[^.!?\n]*",
        ]

        for pattern in patterns_to_remove:
            full_response = re.sub(pattern, "", full_response, flags=re.IGNORECASE)

        # Убираем лишние пробелы и переносы строк после удаления
        full_response = re.sub(r"\s+", " ", full_response)
        full_response = re.sub(r"\n\s*\n", "\n", full_response)
        full_response = full_response.strip()

        if intent.kind == "table":
            # Формируем своё короткое объяснение для таблиц умножения
            table_numbers = []
            # Сначала берем числа, которые IntentService сохранил явно
            table_numbers_attr = getattr(intent, "table_numbers", [])
            if table_numbers_attr:
                table_numbers = [n for n in table_numbers_attr if isinstance(n, int)]
            elif intent.items:
                table_numbers = [n for n in intent.items if isinstance(n, int)]
            elif multiplication_number:
                table_numbers = [multiplication_number]

            if table_numbers:
                if len(table_numbers) == 1:
                    n = table_numbers[0]
                    full_response = (
                        f"Это таблица умножения на {n}. "
                        "Используй её для быстрого счёта: чтобы узнать, чему равно "
                        f"{n}×5, найди строку с числом {n} и столбец с числом 5."
                    )
                else:
                    nums_str = ", ".join(str(n) for n in table_numbers)
                    full_response = (
                        f"Это таблицы умножения на {nums_str}. "
                        "Выбирай нужное число в заголовке и смотри строку и столбец, "
                        "чтобы быстро находить результат."
                    )
            else:
                full_response = "Используй эту таблицу для быстрого счёта."

        elif intent.kind == "both":
            # Смешанный запрос: и таблица, и график.
            # Полностью формируем собственное короткое пояснение, игнорируя текст модели.
            logger.info(
                f"🔍 Stream: Обработка kind='both', intent.items={intent.items}, "
                f"table_numbers={getattr(intent, 'table_numbers', None)}, "
                f"graph_functions={getattr(intent, 'graph_functions', None)}"
            )
            table_numbers: list[int] = []
            table_numbers_attr = getattr(intent, "table_numbers", [])
            if table_numbers_attr:
                table_numbers = [n for n in table_numbers_attr if isinstance(n, int)]
            elif intent.items:
                table_numbers = [n for n in intent.items if isinstance(n, int)]
            elif multiplication_number:
                table_numbers = [multiplication_number]

            # Определяем краткое описание графика
            graph_description = "график функции"
            graph_functions_attr = getattr(intent, "graph_functions", None)
            source_funcs = (
                graph_functions_attr
                if graph_functions_attr
                else (intent.items if intent.items else [])
            )
            if source_funcs:
                first_item = source_funcs[0]
                if isinstance(first_item, str):
                    if "sin" in first_item:
                        graph_description = "график синусоиды"
                    else:
                        graph_description = f"график функции {first_item}"

            parts: list[str] = []

            if table_numbers:
                if len(table_numbers) == 1:
                    n = table_numbers[0]
                    parts.append(
                        f"Это таблица умножения на {n}. "
                        f"Сначала посмотри в ней примеры с числом {n}, чтобы вспомнить умножение."
                    )
                else:
                    nums_str = ", ".join(str(n) for n in table_numbers)
                    parts.append(
                        f"Это таблицы умножения на {nums_str}. "
                        "Выбирай нужное число и тренируйся находить ответы по строкам и столбцам."
                    )

            # Описание графика (без "Ниже", так как график уже на картинке)
            if "sin" in graph_description.lower():
                parts.append(
                    "На картинке также показан график синусоиды: "
                    "по горизонтали меняется число x, а по вертикали видно, как меняется значение функции. "
                    "Посмотри, как кривая поднимается и опускается, и попробуй объяснить это своими словами."
                )
            else:
                parts.append(
                    f"На картинке также показан {graph_description}: "
                    "по горизонтали меняется число x, а по вертикали видно, как меняется значение функции. "
                    "Посмотри, как кривая поднимается и опускается, и попробуй объяснить это своими словами."
                )

            full_response = " ".join(parts)

        else:
            # КРИТИЧНО: Удаляем дублирование таблицы умножения текстом (если модель всё же написала)
            multiplication_duplicate_patterns = [
                r"\d+\s*[×x*]\s*\d+\s*=\s*\d+",
                r"\d+\s+\d+\s*=\s*\d+",
            ]
            for pattern in multiplication_duplicate_patterns:
                full_response = re.sub(pattern, "", full_response, flags=re.IGNORECASE)

            # Удаляем множественные пробелы и пустые строки
            full_response = re.sub(r"\s+", " ", full_response)
            full_response = re.sub(r"\n\s*\n", "\n", full_response)

            # Если ответ слишком длинный (больше 2 предложений) - обрезаем до первых 2
            sentences = re.split(r"[.!?]+\s+", full_response.strip())
            if len(sentences) > 2:
                meaningful_sentences = [
                    s.strip() for s in sentences[:2] if s.strip() and len(s.strip()) > 10
                ]
                if meaningful_sentences:
                    full_response = ". ".join(meaningful_sentences)
                    if not full_response.endswith((".", "!", "?")):
                        full_response += "."
                else:
                    full_response = ". ".join(sentences[:2])
                    if not full_response.endswith((".", "!", "?")):
                        full_response += "."

        logger.info(
            f"✅ Stream: Текст обрезан до короткого объяснения (есть визуализация): {full_response[:100]}"
        )
        return full_response
