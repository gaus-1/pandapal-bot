"""
API endpoints для Telegram Mini App
Обеспечивает взаимодействие между React frontend и Python backend
"""

from aiohttp import web
from loguru import logger

from bot.database import get_db
from bot.security.telegram_auth import TelegramWebAppAuth
from bot.services import (
    ChatHistoryService,
    UserService,
)
from bot.services.ai_service_solid import get_ai_service


async def miniapp_auth(request: web.Request) -> web.Response:
    """
    Аутентификация пользователя Mini App.

    POST /api/miniapp/auth
    Body: { "initData": "..." }

    Returns:
        200: { "success": true, "user": {...} }
        400: { "error": "..." }
        403: { "error": "Invalid initData" }
    """
    try:
        data = await request.json()
        init_data = data.get("initData")

        if not init_data:
            return web.json_response({"error": "initData required"}, status=400)

        # Валидация данных от Telegram
        auth_validator = TelegramWebAppAuth()
        validated_data = auth_validator.validate_init_data(init_data)

        if not validated_data:
            return web.json_response({"error": "Invalid initData"}, status=403)

        # Извлекаем данные пользователя
        user_data = auth_validator.extract_user_data(validated_data)

        if not user_data:
            logger.error("❌ Не удалось извлечь user_data из validated_data")
            return web.json_response({"error": "Failed to extract user data"}, status=400)

        telegram_id = user_data.get("id")

        if not telegram_id:
            logger.error(f"❌ telegram_id отсутствует в user_data: {user_data}")
            return web.json_response({"error": "No user ID in initData"}, status=400)

        # Получаем или создаем пользователя
        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_or_create_user(
                telegram_id=telegram_id,
                username=user_data.get("username"),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
            )

            # Вызываем to_dict() ВНУТРИ сессии
            user_dict = user.to_dict()

        # Возвращаем данные пользователя
        return web.json_response(
            {
                "success": True,
                "user": user_dict,
            }
        )

    except Exception as e:
        logger.error(f"❌ Ошибка аутентификации Mini App: {e}", exc_info=True)
        return web.json_response({"error": f"Internal server error: {str(e)}"}, status=500)


async def miniapp_get_user(request: web.Request) -> web.Response:
    """
    Получить профиль пользователя.

    GET /api/miniapp/user/{telegram_id}
    """
    try:
        telegram_id = int(request.match_info["telegram_id"])

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            user_dict = user.to_dict()

        return web.json_response(
            {
                "success": True,
                "user": user_dict,
            }
        )

    except Exception as e:
        logger.error(f"❌ Ошибка получения пользователя: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_update_user(request: web.Request) -> web.Response:
    """
    Обновить профиль пользователя.

    PATCH /api/miniapp/user/{telegram_id}
    Body: { "age": 10, "grade": 4 }
    """
    try:
        telegram_id = int(request.match_info["telegram_id"])
        data = await request.json()

        age = data.get("age")
        grade = data.get("grade")

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.update_user_profile(telegram_id=telegram_id, age=age, grade=grade)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            user_dict = user.to_dict()

        return web.json_response(
            {
                "success": True,
                "user": user_dict,
            }
        )

    except Exception as e:
        logger.error(f"❌ Ошибка обновления пользователя: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_progress(request: web.Request) -> web.Response:
    """
    Получить прогресс обучения пользователя.

    GET /api/miniapp/progress/{telegram_id}
    """
    try:
        telegram_id = int(request.match_info["telegram_id"])

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Получаем прогресс из БД ВНУТРИ сессии
            progress_items = [p.to_dict() for p in user.progress]

        return web.json_response({"success": True, "progress": progress_items})

    except Exception as e:
        logger.error(f"❌ Ошибка получения прогресса: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_achievements(request: web.Request) -> web.Response:
    """
    Получить достижения пользователя.

    GET /api/miniapp/achievements/{telegram_id}
    """
    try:
        telegram_id = int(request.match_info["telegram_id"])

        # Временные данные (в будущем из БД)
        achievements = [
            {
                "id": "1",
                "title": "Первые шаги",
                "description": "Отправь первое сообщение боту",
                "icon": "🌟",
                "unlocked": True,
                "unlock_date": "2025-01-01T00:00:00Z",
            },
            {
                "id": "2",
                "title": "Знаток математики",
                "description": "Реши 10 задач по математике",
                "icon": "🧮",
                "unlocked": False,
            },
            {
                "id": "3",
                "title": "Полиглот",
                "description": "Изучи 3 языка",
                "icon": "🗣️",
                "unlocked": False,
            },
        ]

        return web.json_response({"success": True, "achievements": achievements})

    except Exception as e:
        logger.error(f"❌ Ошибка получения достижений: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_dashboard(request: web.Request) -> web.Response:
    """
    Получить статистику для дашборда.

    GET /api/miniapp/dashboard/{telegram_id}
    """
    try:
        telegram_id = int(request.match_info["telegram_id"])

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Собираем статистику
            stats = {
                "total_messages": len(user.messages),
                "learning_sessions": len(user.sessions),
                "total_points": sum(p.points for p in user.progress),
                "subjects_studied": len(user.progress),
                "current_streak": 1,  # Временно hardcode
            }

            return web.json_response({"success": True, "stats": stats})

    except Exception as e:
        logger.error(f"❌ Ошибка получения дашборда: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_ai_chat(request: web.Request) -> web.Response:
    """
    Отправить сообщение AI и получить ответ.

    POST /api/miniapp/ai/chat
    Body: { "telegram_id": 123, "message": "..." }
    """
    try:
        data = await request.json()
        telegram_id = data.get("telegram_id")
        message = data.get("message")

        if not telegram_id or not message:
            return web.json_response({"error": "telegram_id and message required"}, status=400)

        with get_db() as db:
            user_service = UserService(db)
            history_service = ChatHistoryService(db)

            user = user_service.get_user_by_telegram_id(telegram_id)
            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Загружаем историю для контекста
            history = history_service.get_formatted_history_for_ai(telegram_id, limit=20)

            # Генерируем ответ AI
            ai_service = get_ai_service()
            ai_response = await ai_service.generate_response(
                user_message=message, chat_history=history, user_age=user.age
            )

            # Сохраняем в историю
            history_service.add_message(telegram_id, message, "user")
            history_service.add_message(telegram_id, ai_response, "ai")

            return web.json_response({"success": True, "response": ai_response})

    except Exception as e:
        logger.error(f"❌ Ошибка AI чата: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_chat_history(request: web.Request) -> web.Response:
    """
    Получить историю чата.

    GET /api/miniapp/chat/history/{telegram_id}?limit=50
    """
    try:
        telegram_id = int(request.match_info["telegram_id"])
        limit = int(request.query.get("limit", "50"))

        with get_db() as db:
            history_service = ChatHistoryService(db)
            messages = history_service.get_recent_history(telegram_id, limit=limit)

            history = [
                {
                    "role": "user" if msg.message_type == "user" else "ai",
                    "content": msg.message_text,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                }
                for msg in messages
            ]

            return web.json_response({"success": True, "history": history})

    except Exception as e:
        logger.error(f"❌ Ошибка получения истории: {e}", exc_info=True)
        return web.json_response({"error": f"Internal server error: {str(e)}"}, status=500)


async def miniapp_get_subjects(request: web.Request) -> web.Response:
    """
    Получить список предметов.

    GET /api/miniapp/subjects
    """
    try:
        # Предметы (в будущем можно вынести в БД)
        subjects = [
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

        return web.json_response({"success": True, "subjects": subjects})

    except Exception as e:
        logger.error(f"❌ Ошибка получения предметов: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_parent_children(request: web.Request) -> web.Response:
    """
    Получить данные детей для родительского дашборда.

    GET /api/miniapp/parent/children/{parent_telegram_id}
    """
    try:
        parent_telegram_id = int(request.match_info["parent_telegram_id"])

        with get_db() as db:
            user_service = UserService(db)

            # Проверяем что пользователь родитель
            parent = user_service.get_user_by_telegram_id(parent_telegram_id)
            if not parent or parent.user_type != "parent":
                return web.json_response({"error": "User is not a parent"}, status=403)

            # Получаем детей
            children = user_service.get_user_children(parent_telegram_id)

            children_data = []
            for child in children:
                # Генерируем данные для дашборда
                weekly_activity = [
                    {"day": "Пн", "messages": 15, "sessions": 3},
                    {"day": "Вт", "messages": 22, "sessions": 5},
                    {"day": "Ср", "messages": 18, "sessions": 4},
                    {"day": "Чт", "messages": 25, "sessions": 6},
                    {"day": "Пт", "messages": 20, "sessions": 4},
                    {"day": "Сб", "messages": 30, "sessions": 7},
                    {"day": "Вс", "messages": 12, "sessions": 2},
                ]

                subjects_progress = [
                    {
                        "subject": "Математика",
                        "points": child.progress[0].points if child.progress else 450,
                        "level": 5,
                    },
                    {"subject": "Русский", "points": 380, "level": 4},
                    {"subject": "Английский", "points": 320, "level": 3},
                    {"subject": "История", "points": 280, "level": 3},
                ]

                children_data.append(
                    {
                        "child_id": child.telegram_id,
                        "child_name": child.first_name or "Ребенок",
                        "total_messages": len(child.messages),
                        "learning_sessions": len(child.sessions),
                        "total_points": sum(p.points for p in child.progress),
                        "subjects_studied": len(child.progress),
                        "current_streak": 5,
                        "weekly_activity": weekly_activity,
                        "subjects_progress": subjects_progress,
                        "safety_score": 95,
                        "last_active": (child.created_at.isoformat() if child.created_at else None),
                    }
                )

            return web.json_response({"success": True, "children": children_data})

    except Exception as e:
        logger.error(f"❌ Ошибка получения данных детей: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


def setup_miniapp_routes(app: web.Application) -> None:
    """
    Регистрация роутов Mini App в aiohttp приложении.

    Args:
        app: aiohttp приложение
    """
    # Аутентификация
    app.router.add_post("/api/miniapp/auth", miniapp_auth)

    # Пользователь
    app.router.add_get("/api/miniapp/user/{telegram_id}", miniapp_get_user)
    app.router.add_patch("/api/miniapp/user/{telegram_id}", miniapp_update_user)

    # Прогресс и достижения
    app.router.add_get("/api/miniapp/progress/{telegram_id}", miniapp_get_progress)
    app.router.add_get("/api/miniapp/achievements/{telegram_id}", miniapp_get_achievements)
    app.router.add_get("/api/miniapp/dashboard/{telegram_id}", miniapp_get_dashboard)

    # AI чат
    app.router.add_post("/api/miniapp/ai/chat", miniapp_ai_chat)
    app.router.add_get("/api/miniapp/chat/history/{telegram_id}", miniapp_get_chat_history)

    # Предметы
    app.router.add_get("/api/miniapp/subjects", miniapp_get_subjects)

    # Родительский дашборд
    app.router.add_get("/api/miniapp/parent/children/{parent_telegram_id}", miniapp_parent_children)

    logger.info("✅ Mini App API routes зарегистрированы")
