"""
Endpoints для логов, предметов и истории чата.
"""

import json
import random
from contextlib import suppress

from aiohttp import web
from loguru import logger

from bot.api.validators import require_owner, validate_limit, validate_telegram_id
from bot.database import get_db
from bot.services import ChatHistoryService


async def miniapp_get_chat_history(request: web.Request) -> web.Response:
    """
    Получить историю чата.

    GET /api/miniapp/chat/history/{telegram_id}?limit=50
    Требует заголовок X-Telegram-Init-Data для проверки владельца ресурса.
    """
    try:
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

        # Проверка владельца ресурса (OWASP A01)
        if error_response := require_owner(request, telegram_id):
            return error_response

        # Безопасная валидация limit
        limit = validate_limit(request.query.get("limit"), default=50, max_limit=100)

        with get_db() as db:
            history_service = ChatHistoryService(db)
            messages = history_service.get_recent_history(telegram_id, limit=limit)

            history = [
                {
                    "role": "user" if msg.message_type == "user" else "ai",
                    "content": msg.message_text,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    "imageUrl": msg.image_url if msg.image_url else None,
                }
                for msg in messages
            ]

            # НЕ добавляем приветствие автоматически - фронтенд сам управляет временем отправки
            # Приветствие будет отправлено через 5 секунд после показа welcome screen

            return web.json_response({"success": True, "history": history})

    except Exception as e:
        logger.error(f"❌ Ошибка получения истории: {e}", exc_info=True)
        return web.json_response({"error": f"Internal server error: {str(e)}"}, status=500)


async def miniapp_clear_chat_history(request: web.Request) -> web.Response:
    """
    Очистить историю чата.

    DELETE /api/miniapp/chat/history/{telegram_id}
    Требует заголовок X-Telegram-Init-Data для проверки владельца ресурса.
    """
    try:
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

        # Проверка владельца ресурса (OWASP A01)
        if error_response := require_owner(request, telegram_id):
            return error_response

        with get_db() as db:
            history_service = ChatHistoryService(db)
            deleted_count = history_service.clear_history(telegram_id)

            db.commit()

            logger.info(f"🗑️ Очищена история для {telegram_id}: {deleted_count} сообщений")
            logger.info("ℹ️ История очищена, приветствие будет отправлено фронтендом")

            return web.json_response({"success": True, "deleted_count": deleted_count})

    except Exception as e:
        logger.error(f"❌ Ошибка очистки истории: {e}", exc_info=True)
        return web.json_response({"error": f"Internal server error: {str(e)}"}, status=500)


async def miniapp_add_greeting(request: web.Request) -> web.Response:
    """
    Добавить приветственное сообщение от бота в историю чата.

    POST /api/miniapp/chat/greeting/{telegram_id}
    Body: { "message": "Привет, начнем?" } (опционально)
    Требует заголовок X-Telegram-Init-Data для проверки владельца ресурса.
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])

        # Проверка владельца ресурса (OWASP A01)
        if error_response := require_owner(request, telegram_id):
            return error_response

        # Парсим тело запроса (может быть пустым)
        greeting_message = None
        try:
            data = await request.json()
            greeting_message = data.get("message") if data else None
        except Exception:
            # Если тело пустое или не JSON - это нормально
            pass

        # Если сообщение не указано, выбираем случайное
        if not greeting_message:
            greetings = [
                "Привет, начнем?",
                "Привет, спроси меня что угодно по любому предмету",
                "Привет! Я готов помочь тебе",
            ]
            greeting_message = random.choice(greetings)

        with get_db() as db:
            history_service = ChatHistoryService(db)

            # Проверяем, что история пустая (только для безопасности)
            messages = history_service.get_recent_history(telegram_id, limit=1)
            if messages:
                logger.info(f"ℹ️ История не пустая, приветствие не добавлено: user={telegram_id}")
                return web.json_response(
                    {"success": False, "message": "History is not empty"}, status=400
                )

            # Добавляем приветственное сообщение от бота
            history_service.add_message(telegram_id, greeting_message, "ai")
            db.commit()

            logger.info(
                f"👋 Приветственное сообщение добавлено: user={telegram_id}, message={greeting_message}"
            )

            return web.json_response({"success": True, "message": greeting_message, "role": "ai"})

    except Exception as e:
        logger.error(f"❌ Ошибка добавления приветствия: {e}", exc_info=True)
        return web.json_response({"error": f"Internal server error: {str(e)}"}, status=500)


async def miniapp_log(request: web.Request) -> web.Response:
    """
    Принять логи с фронтенда для отладки.

    POST /api/miniapp/log
    Body: {
        "level": "log" | "error" | "warn" | "info",
        "message": "текст сообщения",
        "data": {...},  # опционально
        "telegram_id": 123,  # опционально
        "user_agent": "...",  # опционально
    }
    """
    try:
        # Проверяем Content-Type
        content_type = request.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            logger.warning(f"⚠️ Неверный Content-Type для /api/miniapp/log: {content_type}")
            return web.json_response(
                {"success": False, "error": "Invalid Content-Type"}, status=400
            )

        # Пытаемся прочитать JSON
        raw_body = None
        try:
            raw_body = await request.read()
            if not raw_body:
                logger.warning("⚠️ Пустое тело запроса в /api/miniapp/log")
                return web.json_response(
                    {"success": False, "error": "Empty request body"}, status=400
                )

            # Логируем сырые данные для отладки
            raw_body_str = raw_body.decode("utf-8")
            logger.debug(f"📊 Сырое тело запроса (первые 500 символов): {raw_body_str[:500]}")

            data = json.loads(raw_body_str)

            # Логируем распарсенные данные
            logger.debug(f"📊 Распарсенные данные: {str(data)[:500]}")
        except json.JSONDecodeError as json_err:
            logger.warning(f"⚠️ Невалидный JSON в /api/miniapp/log: {json_err}")
            return web.json_response({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as read_err:
            logger.warning(f"⚠️ Ошибка чтения тела запроса /api/miniapp/log: {read_err}")
            return web.json_response(
                {"success": False, "error": "Failed to read request body"}, status=400
            )

        # Извлекаем данные с безопасными значениями по умолчанию
        if not isinstance(data, dict):
            logger.warning(f"⚠️ Данные не являются словарем: {type(data)}")
            return web.json_response({"success": False, "error": "Invalid data format"}, status=400)

        level = data.get("level", "log")
        if level not in ("log", "error", "warn", "info", "debug"):
            level = "log"

        message = data.get("message", "")
        # Безопасно извлекаем log_data - может быть словарем или другим типом
        log_data = None
        try:
            log_data = data.get("data")
        except Exception as get_data_err:
            logger.debug(
                f"⚠️ Ошибка получения data из запроса: {type(get_data_err).__name__}: {get_data_err}"
            )
            log_data = None

        # Безопасная обработка log_data
        try:
            if log_data is None:
                log_data = {}
            elif isinstance(log_data, str):
                # Если это строка (например, JSON строка), пытаемся распарсить
                try:
                    parsed = json.loads(log_data)
                    log_data = parsed if isinstance(parsed, dict) else {"value": str(parsed)[:500]}
                except Exception as parse_err:
                    # Если не JSON, просто строка
                    logger.debug(f"⚠️ Не удалось распарсить log_data как JSON: {parse_err}")
                    log_data = {"value": log_data[:500]}
            elif not isinstance(log_data, dict):
                # Если это не словарь, преобразуем в словарь с одним ключом
                try:
                    log_data = {"value": str(log_data)[:500]}  # Ограничиваем размер
                except Exception:
                    log_data = {"value": "<unserializable>"}
        except Exception as process_err:
            # Если произошла ошибка при обработке, просто создаем пустой словарь
            logger.debug(
                f"⚠️ Ошибка обработки log_data: {type(process_err).__name__}: {process_err}"
            )
            log_data = {}

        telegram_id = data.get("telegram_id")
        user_agent = data.get("user_agent", request.headers.get("User-Agent", "Unknown"))

        # Формируем лог сообщение
        log_prefix = f"📱 Frontend [{level.upper()}]"
        if telegram_id:
            log_prefix += f" user={telegram_id}"
        log_message = f"{log_prefix}: {message}"

        # Добавляем данные если есть
        if log_data:
            try:
                # ПРОСТОЕ РЕШЕНИЕ: используем json.dumps с безопасной функцией default
                def safe_str(obj):
                    """Безопасная функция для преобразования объектов в строку"""
                    try:
                        return str(obj)
                    except Exception:
                        return "<unserializable>"

                try:
                    # Пытаемся сериализовать через JSON
                    if isinstance(log_data, dict):
                        data_str = json.dumps(log_data, ensure_ascii=False, default=safe_str)
                    else:
                        data_str = safe_str(log_data)

                    if len(data_str) > 1000:
                        data_str = data_str[:1000] + "... (truncated)"
                    log_message += f" | data={data_str}"
                except (KeyError, TypeError, ValueError) as json_err:
                    # Если произошла ошибка при сериализации, просто пропускаем данные
                    logger.debug(
                        f"⚠️ Не удалось сериализовать log_data: {type(json_err).__name__}: {json_err}"
                    )
                    pass
                except Exception as json_err:
                    # Для любых других ошибок тоже пропускаем
                    logger.debug(
                        f"⚠️ Неожиданная ошибка при сериализации log_data: {type(json_err).__name__}: {json_err}"
                    )
                    pass
            except Exception as e:
                # Если не удалось сериализовать, просто пропускаем данные
                logger.debug(f"⚠️ Общая ошибка обработки log_data: {type(e).__name__}: {e}")
                pass

        # Логируем в зависимости от уровня
        try:
            # Упрощаем логирование - убираем extra, чтобы избежать проблем
            if level == "error":
                logger.error(log_message)
            elif level == "warn":
                logger.warning(log_message)
            elif level == "info":
                logger.info(log_message)
            else:
                logger.debug(log_message)
        except Exception as log_err:
            # Если не удалось залогировать, просто логируем ошибку без форматирования
            from contextlib import suppress

            with suppress(Exception):
                logger.debug(f"⚠️ Ошибка логирования: {type(log_err).__name__}: {str(log_err)}")

        return web.json_response({"success": True})

    except KeyError as key_err:
        # Специальная обработка KeyError - логируем детали
        error_msg = str(key_err)
        logger.error(f"❌ KeyError при приеме лога с фронтенда: {error_msg}", exc_info=True)
        # Логируем сырые данные, если они были прочитаны
        try:
            if "raw_body" in locals() and raw_body:
                logger.debug(f"📊 Сырые данные запроса (первые 500 символов): {raw_body[:500]}")
            if "data" in locals():
                logger.debug(f"📊 Распарсенные данные (первые 500 символов): {str(data)[:500]}")
        except Exception:
            pass
        # Возвращаем 200, чтобы не засорять консоль фронтенда ошибками
        return web.json_response({"success": False, "error": "Internal server error"}, status=200)
    except Exception as e:
        # Детальное логирование ошибки для отладки
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(f"❌ Ошибка приема лога с фронтенда: {error_type}: {error_msg}", exc_info=True)
        # Логируем сырые данные, если они были прочитаны
        try:
            if "raw_body" in locals() and raw_body:
                logger.debug(f"📊 Сырые данные запроса (первые 500 символов): {raw_body[:500]}")
        except Exception:
            pass
        # Возвращаем 200, чтобы не засорять консоль фронтенда ошибками
        return web.json_response({"success": False, "error": "Internal server error"}, status=200)


async def miniapp_get_subjects(request: web.Request) -> web.Response:
    """
    Получить список предметов с учетом Premium статуса.

    GET /api/miniapp/subjects?telegram_id=123
    """
    try:
        # Валидация telegram_id из query (опционально)
        telegram_id_str = request.query.get("telegram_id")
        if telegram_id_str:
            with suppress(ValueError):
                validate_telegram_id(telegram_id_str)

        # Все предметы школьной программы (ФГОС). Доступ ко всем — бесплатно 30 запросов/мес.
        all_subjects = [
            {
                "id": "russian",
                "name": "Русский язык",
                "icon": "📝",
                "description": "Грамматика, орфография, пунктуация",
                "grade_range": [1, 11],
            },
            {
                "id": "literature",
                "name": "Литература",
                "icon": "📖",
                "description": "Чтение, анализ текста, сочинения",
                "grade_range": [1, 11],
            },
            {
                "id": "math",
                "name": "Математика",
                "icon": "🧮",
                "description": "Алгебра, геометрия, вероятность и статистика",
                "grade_range": [1, 11],
            },
            {
                "id": "foreign_lang",
                "name": "Иностранный язык",
                "icon": "🌐",
                "description": "Английский, немецкий, французский, испанский",
                "grade_range": [1, 11],
            },
            {
                "id": "foreign_lang_2",
                "name": "Второй иностранный язык",
                "icon": "🗣️",
                "description": "По выбору школы",
                "grade_range": [5, 11],
            },
            {
                "id": "native_lang",
                "name": "Родной язык",
                "icon": "📜",
                "description": "По заявлению родителей",
                "grade_range": [1, 11],
            },
            {
                "id": "native_literature",
                "name": "Родная литература",
                "icon": "📚",
                "description": "По заявлению родителей",
                "grade_range": [1, 11],
            },
            {
                "id": "history",
                "name": "История",
                "icon": "🏛️",
                "description": "История России, всеобщая история, история родного края",
                "grade_range": [5, 11],
            },
            {
                "id": "social_studies",
                "name": "Обществознание",
                "icon": "👥",
                "description": "Общество, право, экономика, политика",
                "grade_range": [5, 11],
            },
            {
                "id": "geography",
                "name": "География",
                "icon": "🌍",
                "description": "Страны, континенты, природа",
                "grade_range": [5, 11],
            },
            {
                "id": "physics",
                "name": "Физика",
                "icon": "⚡",
                "description": "Механика, оптика, электричество",
                "grade_range": [7, 11],
            },
            {
                "id": "chemistry",
                "name": "Химия",
                "icon": "⚗️",
                "description": "Неорганика, органика, реакции",
                "grade_range": [8, 11],
            },
            {
                "id": "biology",
                "name": "Биология",
                "icon": "🧬",
                "description": "Ботаника, зоология, анатомия",
                "grade_range": [5, 11],
            },
            {
                "id": "informatics",
                "name": "Информатика",
                "icon": "💻",
                "description": "Алгоритмы, программирование, работа с данными",
                "grade_range": [1, 11],
            },
            {
                "id": "world_around",
                "name": "Окружающий мир / Природоведение",
                "icon": "🌿",
                "description": "Природа, человек, общество",
                "grade_range": [1, 5],
            },
            {
                "id": "obzh",
                "name": "Основы безопасности жизнедеятельности (ОБЖ)",
                "icon": "🛡️",
                "description": "Безопасность, первая помощь, гражданская оборона",
                "grade_range": [5, 11],
            },
            {
                "id": "pe",
                "name": "Физическая культура",
                "icon": "⚽",
                "description": "Спорт, здоровый образ жизни",
                "grade_range": [1, 11],
            },
            {
                "id": "technology",
                "name": "Технология (Труд)",
                "icon": "🔧",
                "description": "Труд, проекты, конструирование",
                "grade_range": [1, 11],
            },
            {
                "id": "art",
                "name": "Изобразительное искусство",
                "icon": "🎨",
                "description": "Рисование, живопись, композиция",
                "grade_range": [1, 7],
            },
            {
                "id": "music",
                "name": "Музыка",
                "icon": "🎵",
                "description": "Музыкальная грамота, пение, слушание",
                "grade_range": [1, 7],
            },
            {
                "id": "orkse",
                "name": "Основы религиозных культур и светской этики (ОРКСЭ)",
                "icon": "☯️",
                "description": "Модули по выбору, 4–5 класс",
                "grade_range": [4, 5],
            },
            {
                "id": "odnkr",
                "name": "Основы духовно-нравственной культуры России (ОДНКР)",
                "icon": "🇷🇺",
                "description": "Культура, традиции, нравственность",
                "grade_range": [5, 9],
            },
        ]

        return web.json_response({"success": True, "subjects": all_subjects})

    except Exception as e:
        logger.error(f"❌ Ошибка получения предметов: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)
