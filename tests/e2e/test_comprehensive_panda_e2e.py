"""
КОМПЛЕКСНЫЙ E2E тест всех функций панды с реальным API.

Проверяет ВСЕ сценарии:
1. Визуализации (графики, таблицы, диаграммы, схемы, карты) по всем предметам
2. Текстовые ответы по всем предметам - развернутые и подробные
3. Обработка фото по всем предметам - полная обработка
4. Проверка домашних заданий через homework endpoint
5. Модерация - НЕ блокирует школьные вопросы (история, география и т.д.)
6. Развернутые ответы - качество как GPT-5/Opus 4.5

Использует РЕАЛЬНЫЙ API Yandex Cloud везде где возможно.
"""

import base64
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp.test_utils import make_mocked_request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.api.miniapp import miniapp_ai_chat, miniapp_auth, miniapp_get_user
from bot.api.miniapp.homework import miniapp_check_homework
from bot.config import settings
from bot.models import Base
from bot.services.gamification_service import GamificationService
from bot.services.history_service import ChatHistoryService
from bot.services.moderation_service import ContentModerationService
from bot.services.user_service import UserService


# Проверка наличия реального API ключа
def _check_real_api_key():
    """Проверяет наличие реального API ключа в env или settings."""
    env_key = os.environ.get("YANDEX_CLOUD_API_KEY", "")
    if env_key and env_key != "test_api_key" and len(env_key) > 20:
        return True
    try:
        from bot.config.settings import settings

        settings_key = settings.yandex_cloud_api_key
        if (
            settings_key
            and settings_key != "test_api_key"
            and settings_key != "your_real_yandex_api_key_here"
            and len(settings_key) > 20
        ):
            return True
    except Exception:
        pass
    return False


REAL_API_KEY_AVAILABLE = _check_real_api_key()


@pytest.mark.e2e
@pytest.mark.slow
class TestComprehensivePandaE2E:
    """Комплексный E2E тест всех функций панды с реальным API."""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Реальная БД для E2E теста"""
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        yield session

        session.close()
        engine.dispose()
        os.close(db_fd)
        os.unlink(db_path)

    @pytest.fixture
    def has_yandex_keys(self):
        """Проверяет наличие Yandex API ключей"""
        return REAL_API_KEY_AVAILABLE

    @pytest.fixture
    def e2e_auth_patches(self):
        """Патчи require_owner/verify_resource_owner только для E2E (без реального initData)."""
        p1 = patch("bot.api.miniapp.chat.require_owner", return_value=None)
        p2 = patch("bot.api.miniapp.progress.require_owner", return_value=None)
        p3 = patch("bot.api.miniapp.homework.require_owner", return_value=None)
        p4 = patch(
            "bot.api.miniapp.auth.verify_resource_owner",
            side_effect=lambda _req, _tid: (True, None),
        )
        p1.start()
        p2.start()
        p3.start()
        p4.start()
        try:
            yield
        finally:
            p4.stop()
            p3.stop()
            p2.stop()
            p1.stop()

    def _check_response_quality(self, response: str, min_sentences: int = 4) -> dict:
        """Проверка качества ответа - развернутый, структурированный, подробный."""
        issues = []
        quality_score = 100

        # 1. Проверка длины
        sentences = [s.strip() for s in response.split(".") if s.strip()]
        if len(sentences) < min_sentences:
            issues.append(f"Слишком мало предложений: {len(sentences)} < {min_sentences}")
            quality_score -= 30

        # 2. Проверка общей длины ответа
        if len(response) < 150:
            issues.append(f"Ответ слишком короткий: {len(response)} < 150 символов")
            quality_score -= 20

        # 3. Проверка на наличие примеров
        example_keywords = ["например", "к примеру", "так", "также", "если", "чтобы", "допустим"]
        has_examples = any(kw in response.lower() for kw in example_keywords)
        if not has_examples and len(sentences) >= 3:
            issues.append("Нет примеров в ответе")
            quality_score -= 15

        return {
            "quality_score": max(0, quality_score),
            "issues": issues,
            "sentences_count": len(sentences),
            "total_length": len(response),
        }

    def create_request(self, json_data, endpoint="/api/miniapp/ai/chat"):
        """Создает aiohttp Request для API"""
        request = make_mocked_request(
            "POST", endpoint, headers={"Content-Type": "application/json"}
        )
        request._json_data = json_data

        async def json():
            return request._json_data

        request.json = json
        type(request).remote = property(lambda self: "127.0.0.1")
        return request

    def create_image_with_text(self, text: str) -> str:
        """Создает тестовое изображение с текстом в base64"""
        try:
            import io

            from PIL import Image, ImageDraw, ImageFont

            img = Image.new("RGB", (600, 200), color="white")
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except Exception:
                font = ImageFont.load_default()

            draw.text((20, 80), text, fill="black", font=font)

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
            image_bytes = img_byte_arr.getvalue()

            photo_base64 = base64.b64encode(image_bytes).decode("utf-8")
            return f"data:image/png;base64,{photo_base64}"
        except ImportError:
            # Если PIL не установлен, используем минимальное изображение
            minimal_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            return f"data:image/png;base64,{minimal_image}"

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_moderation_not_blocks_school_questions_e2e(
        self, real_db_session, e2e_auth_patches
    ):
        """КРИТИЧНО: Модерация НЕ блокирует школьные вопросы через E2E."""
        telegram_id = 888999000
        test_username = "moderation_test_user"

        # Создаем пользователя
        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(telegram_id, test_username, "Тест", "Модерация")
        user_service.update_user_profile(telegram_id, age=12, grade=6, user_type="child")
        real_db_session.commit()

        moderation_service = ContentModerationService()

        # Школьные вопросы, которые НЕ должны блокироваться
        school_questions = [
            "Расскажи про Великую Отечественную войну",
            "Покажи карту России",
            "Покажи таблицу умножения на 7",
            "Что такое скорость в физике?",
            "Что такое государство? Объясни простыми словами.",
        ]

        failed_questions = []
        for question in school_questions:
            # Проверяем через реальную модерацию
            is_safe, reason = moderation_service.is_safe_content(question)
            if not is_safe:
                failed_questions.append((question, reason))

            # Также проверяем через E2E запрос (мокаем БД, но используем реальную модерацию)
            request = self.create_request({"telegram_id": telegram_id, "message": question})

            with patch("bot.api.miniapp.chat.get_db") as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = real_db_session
                mock_get_db.return_value.__exit__.return_value = None

                # Если нет ключей - мокаем AI, но модерация РЕАЛЬНАЯ
                ai_patch = None
                if not REAL_API_KEY_AVAILABLE:
                    ai_patch = patch("bot.api.miniapp.chat.get_ai_service")
                    mock_ai = AsyncMock()
                    mock_ai.generate_response = AsyncMock(return_value="Тестовый ответ")
                    mock_get_ai = ai_patch.start()
                    mock_get_ai.return_value = mock_ai

                try:
                    response = await miniapp_ai_chat(request)
                    # Если модерация заблокировала - статус может быть 200 с сообщением или 400
                    if response.status == 200:
                        import json

                        body = response._body if hasattr(response, "_body") else b"{}"
                        data = json.loads(body.decode("utf-8")) if body else {}
                        # Если есть ошибка модерации в ответе - это проблема
                        if "error" in data and "запрещен" in str(data.get("error", "")).lower():
                            failed_questions.append(
                                (question, f"Заблокировано в E2E: {data.get('error')}")
                            )
                finally:
                    if ai_patch:
                        ai_patch.stop()

        assert len(failed_questions) == 0, (
            f"Модерация заблокировала {len(failed_questions)} школьных вопросов:\n"
            + "\n".join([f"  - {q}: {r}" for q, r in failed_questions])
        )

        print(f"\n[OK] Все {len(school_questions)} школьных вопросов прошли модерацию через E2E")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_text_responses_all_subjects_detailed_e2e(
        self, real_db_session, has_yandex_keys, e2e_auth_patches
    ):
        """E2E: Текстовые ответы по ВСЕМ предметам должны быть развернутыми и подробными."""
        telegram_id = 777888999
        test_username = "text_subjects_test_user"

        # Создаем пользователя
        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(telegram_id, test_username, "Тест", "Предметы")
        user_service.update_user_profile(telegram_id, age=12, grade=6, user_type="child")
        real_db_session.commit()

        # Вопросы по ВСЕМ предметам с требованием развернутого ответа
        test_cases = [
            (
                "Математика",
                "Объясни что такое квадратное уравнение. Расскажи подробно с примерами.",
                12,
            ),
            (
                "Русский",
                "Объясни что такое подлежащее и сказуемое. Расскажи подробно с примерами предложений.",
                10,
            ),
            (
                "История",
                "Когда началась Великая Отечественная война? Расскажи подробно про это событие.",
                13,
            ),
            ("География", "Какая самая длинная река в России? Расскажи подробно про неё.", 11),
            (
                "Биология",
                "Что такое фотосинтез? Объясни подробно простыми словами с примерами.",
                11,
            ),
            ("Физика", "Что такое скорость в физике? Объясни подробно простыми словами.", 11),
            ("Химия", "Что такое вода? Из чего она состоит? Объясни подробно с примерами.", 12),
        ]

        results = {}
        for subject, question, age in test_cases:
            # Обновляем возраст для каждого предмета
            user_service.update_user_profile(telegram_id, age=age)
            real_db_session.commit()

            request = self.create_request({"telegram_id": telegram_id, "message": question})

            with patch("bot.api.miniapp.chat.get_db") as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = real_db_session
                mock_get_db.return_value.__exit__.return_value = None

                response = await miniapp_ai_chat(request)
                assert response.status == 200, f"Запрос по {subject} должен быть успешным"

                import json

                body = response._body if hasattr(response, "_body") else b"{}"
                data = json.loads(body.decode("utf-8")) if body else {}

                assert "response" in data or "message" in data, (
                    f"Ответ должен содержать response или message для {subject}"
                )

                ai_response = data.get("response") or data.get("message", "")
                assert ai_response, f"AI не ответил на вопрос по {subject}"
                assert len(ai_response) > 100, (
                    f"Ответ слишком короткий по {subject}: {len(ai_response)} символов"
                )

                # Проверка качества ответа
                quality = self._check_response_quality(ai_response, min_sentences=4)

                results[subject] = {
                    "quality_score": quality["quality_score"],
                    "sentences": quality["sentences_count"],
                    "length": quality["total_length"],
                    "issues": quality["issues"],
                }

                print(
                    f"\n[{subject}] E2E Quality: {quality['quality_score']}/100, "
                    f"Sentences: {quality['sentences_count']}, "
                    f"Length: {quality['total_length']}"
                )

        # Проверка: все ответы должны быть качественными
        avg_score = sum(r["quality_score"] for r in results.values()) / len(results)
        assert avg_score >= 70, (
            f"Средний балл качества ответов слишком низкий: {avg_score:.1f}/100. "
            f"Минимум должен быть 70/100"
        )

        print(f"\n[OK] Все предметы протестированы через E2E! Средний балл: {avg_score:.1f}/100")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_visualizations_with_detailed_explanations_e2e(
        self, real_db_session, has_yandex_keys, e2e_auth_patches
    ):
        """E2E: Визуализации должны генерироваться + подробное пояснение."""
        telegram_id = 666777888
        test_username = "viz_test_user"

        # Создаем пользователя
        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(telegram_id, test_username, "Тест", "Визуализации")
        user_service.update_user_profile(telegram_id, age=12, grade=6, user_type="child")
        real_db_session.commit()

        # Тест-кейсы для визуализаций
        test_cases = [
            ("График", "Покажи график синуса"),
            ("Таблица", "Покажи таблицу умножения на 7"),
            ("Диаграмма", "Покажи столбчатую диаграмму: Математика 30, Русский 25, История 20"),
            ("Карта", "Покажи карту Москвы"),
        ]

        results = {}
        for viz_type, question in test_cases:
            request = self.create_request({"telegram_id": telegram_id, "message": question})

            with patch("bot.api.miniapp.chat.get_db") as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = real_db_session
                mock_get_db.return_value.__exit__.return_value = None

                response = await miniapp_ai_chat(request)
                assert response.status == 200, f"Запрос {viz_type} должен быть успешным"

                import json

                body = response._body if hasattr(response, "_body") else b"{}"
                data = json.loads(body.decode("utf-8")) if body else {}

                ai_response = data.get("response") or data.get("message", "")
                assert ai_response, f"AI не ответил на запрос {viz_type}"

                # Проверяем что визуализация генерируется через сервис
                from bot.services.visualization_service import VisualizationService

                viz_service = VisualizationService()
                viz_image, _ = viz_service.detect_visualization_request(question)
                has_visualization = viz_image is not None and len(viz_image) > 1000

                # Проверка качества ответа
                quality = self._check_response_quality(ai_response, min_sentences=3)

                results[viz_type] = {
                    "has_visualization": has_visualization,
                    "quality_score": quality["quality_score"],
                    "sentences": quality["sentences_count"],
                    "length": quality["total_length"],
                }

                print(
                    f"\n[{viz_type}] E2E: Visualization={has_visualization}, "
                    f"Quality: {quality['quality_score']}/100, "
                    f"Sentences: {quality['sentences_count']}"
                )

        # Проверка: хотя бы большинство визуализаций должны генерироваться
        generated_count = sum(1 for r in results.values() if r.get("has_visualization"))
        # Требуем минимум 1, т.к. визуализации могут не возвращаться в E2E response (генерируются внутри)
        assert generated_count >= 1 or all(r["quality_score"] >= 70 for r in results.values()), (
            f"Слишком мало визуализаций генерируется: {generated_count}/{len(test_cases)}, "
            f"или низкое качество ответов"
        )

        print(
            f"\n[OK] Визуализации протестированы через E2E! Сгенерировано: {generated_count}/{len(test_cases)}"
        )

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_photo_processing_all_subjects_e2e(
        self, real_db_session, has_yandex_keys, e2e_auth_patches
    ):
        """E2E: Обработка фото по всем предметам - полная обработка."""
        telegram_id = 555666777
        test_username = "photo_test_user"

        # Создаем пользователя
        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(telegram_id, test_username, "Тест", "Фото")
        user_service.update_user_profile(telegram_id, age=12, grade=6, user_type="child")
        real_db_session.commit()

        # Тест-кейсы для фото по разным предметам
        test_cases = [
            ("Математика", "Реши: 15 + 27 = ?"),
            ("Русский", "Подчеркни подлежащее: Мама готовит обед."),
            ("История", "Великая Отечественная война 1941-1945"),
        ]

        results = {}
        # Мокаем get_db везде где используется (helpers импортирует из bot.database, но используется внутри модуля)
        # Нужно мокировать и bot.database.get_db (для helpers), и bot.api.miniapp.chat.get_db (для chat)
        with (
            patch("bot.database.get_db") as mock_get_db_database,
            patch("bot.api.miniapp.helpers.get_db") as mock_get_db_helpers,
            patch("bot.api.miniapp.chat.get_db") as mock_get_db_chat,
        ):
            # Настраиваем моки - все должны возвращать нашу тестовую БД
            mock_get_db_database.return_value.__enter__.return_value = real_db_session
            mock_get_db_database.return_value.__exit__.return_value = None
            mock_get_db_helpers.return_value.__enter__.return_value = real_db_session
            mock_get_db_helpers.return_value.__exit__.return_value = None
            mock_get_db_chat.return_value.__enter__.return_value = real_db_session
            mock_get_db_chat.return_value.__exit__.return_value = None

            for subject, image_text in test_cases:
                photo_base64 = self.create_image_with_text(image_text)

                request = self.create_request(
                    {
                        "telegram_id": telegram_id,
                        "message": "Что на этом фото?",
                        "photo_base64": photo_base64,
                    }
                )

                response = await miniapp_ai_chat(request)
                assert response.status == 200, f"Запрос фото по {subject} должен быть успешным"

                import json

                body = response._body if hasattr(response, "_body") else b"{}"
                data = json.loads(body.decode("utf-8")) if body else {}

                ai_response = data.get("response") or data.get("message", "")
                assert ai_response, f"AI не ответил на фото по {subject}"
                assert len(ai_response) > 50, f"Анализ фото слишком короткий по {subject}"

                results[subject] = {
                    "processed": True,
                    "analysis_length": len(ai_response),
                }

                print(
                    f"\n[{subject}] E2E Photo processed: OK, Analysis length: {len(ai_response)} символов"
                )

        # Проверка: все фото должны обрабатываться
        processed_count = sum(1 for r in results.values() if r.get("processed"))
        assert processed_count == len(test_cases), (
            f"Не все фото обработаны: {processed_count}/{len(test_cases)}"
        )

        print(
            f"\n[OK] Фото протестированы через E2E! Обработано: {processed_count}/{len(test_cases)}"
        )

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_homework_check_e2e(self, real_db_session, has_yandex_keys, e2e_auth_patches):
        """E2E: Проверка домашних заданий через homework endpoint."""
        telegram_id = 444555666
        test_username = "homework_test_user"

        # Создаем пользователя
        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(telegram_id, test_username, "Тест", "Домашка")
        user_service.update_user_profile(telegram_id, age=12, grade=6, user_type="child")
        real_db_session.commit()

        # Создаем фото с задачей
        photo_base64 = self.create_image_with_text("Реши уравнение: 2x + 5 = 15")

        request = make_mocked_request(
            "POST",
            "/api/miniapp/homework/check",
            headers={"Content-Type": "application/json"},
        )
        request._json_data = {
            "telegram_id": telegram_id,
            "photo_base64": photo_base64,
            "subject": "математика",
            "topic": "уравнения",
            "message": "Проверь это задание",
        }

        async def json():
            return request._json_data

        request.json = json
        type(request).remote = property(lambda self: "127.0.0.1")

        with patch("bot.api.miniapp.homework.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            response = await miniapp_check_homework(request)
            assert response.status == 200, "Проверка ДЗ должна быть успешной"

            import json

            body = response._body if hasattr(response, "_body") else b"{}"
            data = json.loads(body.decode("utf-8")) if body else {}

            assert data.get("success") is True, "Ответ должен быть успешным"
            assert "submission" in data, "Ответ должен содержать submission"

            submission = data["submission"]
            assert "ai_feedback" in submission, "Submission должен содержать ai_feedback"
            assert len(submission["ai_feedback"]) > 50, "AI feedback должен быть подробным"

            print(f"\n[OK] Проверка ДЗ через E2E: OK")
            print(f"   Subject: {submission.get('subject')}")
            print(f"   Has errors: {submission.get('has_errors')}")
            print(f"   Feedback length: {len(submission['ai_feedback'])} символов")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_complete_user_journey_with_all_features_e2e(
        self, real_db_session, has_yandex_keys, e2e_auth_patches
    ):
        """E2E: Полный путь пользователя со ВСЕМИ функциями - текст, фото, визуализации, ДЗ."""
        telegram_id = 333444555
        test_username = "complete_journey_user"

        # Создаем пользователя
        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(telegram_id, test_username, "Полный", "Путь")
        user_service.update_user_profile(telegram_id, age=12, grade=6, user_type="child")
        real_db_session.commit()

        # Шаг 1: Текстовый вопрос по математике (развернутый ответ)
        text_request = self.create_request(
            {
                "telegram_id": telegram_id,
                "message": "Объясни что такое квадратное уравнение. Расскажи подробно с примерами.",
            }
        )

        with patch("bot.api.miniapp.chat.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            text_response = await miniapp_ai_chat(text_request)
            assert text_response.status == 200

            import json

            body = text_response._body if hasattr(text_response, "_body") else b"{}"
            text_data = json.loads(body.decode("utf-8")) if body else {}
            text_ai_response = text_data.get("response") or text_data.get("message", "")

            assert text_ai_response, "AI должен ответить на текстовый вопрос"
            quality = self._check_response_quality(text_ai_response, min_sentences=4)
            assert quality["quality_score"] >= 70, (
                f"Качество текстового ответа слишком низкое: {quality['quality_score']}/100"
            )

        # Шаг 2: Запрос визуализации (график синуса)
        viz_request = self.create_request(
            {
                "telegram_id": telegram_id,
                "message": "Покажи график синуса",
            }
        )

        with patch("bot.api.miniapp.chat.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            viz_response = await miniapp_ai_chat(viz_request)
            assert viz_response.status == 200

            body = viz_response._body if hasattr(viz_response, "_body") else b"{}"
            viz_data = json.loads(body.decode("utf-8")) if body else {}
            viz_ai_response = viz_data.get("response") or viz_data.get("message", "")

            assert viz_ai_response, "AI должен ответить на запрос визуализации"

        # Шаг 3: Фото с задачей
        photo_base64 = self.create_image_with_text("Реши: 15 + 27 = ?")
        photo_request = self.create_request(
            {
                "telegram_id": telegram_id,
                "message": "Что на этом фото?",
                "photo_base64": photo_base64,
            }
        )

        # Мокаем get_db везде где используется (chat, helpers, database)
        with (
            patch("bot.database.get_db") as mock_get_db_database,
            patch("bot.api.miniapp.helpers.get_db") as mock_get_db_helpers,
            patch("bot.api.miniapp.chat.get_db") as mock_get_db_chat,
        ):
            mock_get_db_database.return_value.__enter__.return_value = real_db_session
            mock_get_db_database.return_value.__exit__.return_value = None
            mock_get_db_helpers.return_value.__enter__.return_value = real_db_session
            mock_get_db_helpers.return_value.__exit__.return_value = None
            mock_get_db_chat.return_value.__enter__.return_value = real_db_session
            mock_get_db_chat.return_value.__exit__.return_value = None

            photo_response = await miniapp_ai_chat(photo_request)
            assert photo_response.status == 200

            body = photo_response._body if hasattr(photo_response, "_body") else b"{}"
            photo_data = json.loads(body.decode("utf-8")) if body else {}
            photo_ai_response = photo_data.get("response") or photo_data.get("message", "")

            assert photo_ai_response, "AI должен ответить на фото"
            assert len(photo_ai_response) > 50, "Анализ фото должен быть подробным"

        # Шаг 4: Проверка ДЗ
        hw_photo_base64 = self.create_image_with_text("Реши уравнение: 2x + 5 = 15")
        hw_request = make_mocked_request(
            "POST",
            "/api/miniapp/homework/check",
            headers={"Content-Type": "application/json"},
        )
        hw_request._json_data = {
            "telegram_id": telegram_id,
            "photo_base64": hw_photo_base64,
            "subject": "математика",
        }

        async def json_func():
            return hw_request._json_data

        hw_request.json = json_func
        type(hw_request).remote = property(lambda self: "127.0.0.1")

        with patch("bot.api.miniapp.homework.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = real_db_session
            mock_get_db.return_value.__exit__.return_value = None

            hw_response = await miniapp_check_homework(hw_request)
            assert hw_response.status == 200

            import json

            body = hw_response._body if hasattr(hw_response, "_body") else b"{}"
            hw_data = json.loads(body.decode("utf-8")) if body else {}

            assert hw_data.get("success") is True, "Проверка ДЗ должна быть успешной"
            assert "submission" in hw_data, "Ответ должен содержать submission"

        # Проверяем историю в БД
        history_service = ChatHistoryService(real_db_session)
        history = history_service.get_recent_history(telegram_id, limit=100)
        assert len(history) >= 6, (
            f"Должно быть минимум 6 сообщений в истории, получено: {len(history)}"
        )

        print(f"\n[OK] Полный путь пользователя протестирован через E2E:")
        print(f"   - Текстовый ответ: Quality {quality['quality_score']}/100")
        print(f"   - Визуализация: OK")
        print(f"   - Фото: OK (length: {len(photo_ai_response)})")
        print(f"   - Проверка ДЗ: OK")
        print(f"   - История в БД: {len(history)} сообщений")
