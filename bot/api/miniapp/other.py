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
        # Получаем telegram_id из query параметров (опционально)
        telegram_id = None
        telegram_id_str = request.query.get("telegram_id")
        if telegram_id_str:
            with suppress(ValueError):
                telegram_id = validate_telegram_id(telegram_id_str)

        # Предметы (в будущем можно вынести в БД)
        all_subjects = [
            {
                "id": "math",
                "name": "Математика",
                "icon": "🧮",
                "description": "Арифметика, алгебра, геометрия",
                "grade_range": [1, 11],
            },
            {
                "id": "russian",
                "name": "Русский язык",
                "icon": "📝",
                "description": "Грамматика, орфография, пунктуация",
                "grade_range": [1, 11],
            },
            {
                "id": "english",
                "name": "Английский язык",
                "icon": "🇬🇧",
                "description": "Vocabulary, grammar, conversation",
                "grade_range": [1, 11],
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
                "id": "geography",
                "name": "География",
                "icon": "🌍",
                "description": "Страны, континенты, природа",
                "grade_range": [5, 11],
            },
            {
                "id": "history",
                "name": "История",
                "icon": "📚",
                "description": "Древний мир, средние века, новое время",
                "grade_range": [5, 11],
            },
        ]

        # Если telegram_id указан, проверяем Premium и ограничиваем доступ
        if telegram_id:
            with get_db() as db:
                from bot.services.premium_features_service import PremiumFeaturesService

                premium_service = PremiumFeaturesService(db)
                is_premium = premium_service.is_premium_active(telegram_id)

                # Для бесплатных - только базовые предметы
                if not is_premium:
                    free_subjects_ids = ["math", "russian", "english"]
                    subjects = [s for s in all_subjects if s["id"] in free_subjects_ids]
                    # Добавляем информацию о premium для остальных
                    for subject in all_subjects:
                        if subject["id"] not in free_subjects_ids:
                            subject["premium_required"] = True
                            subject["locked"] = True
                else:
                    subjects = all_subjects
        else:
            # Если telegram_id не указан, возвращаем все предметы
            subjects = all_subjects

        return web.json_response({"success": True, "subjects": subjects})

    except Exception as e:
        logger.error(f"❌ Ошибка получения предметов: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)
