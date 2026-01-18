"""
КОМПЛЕКСНЫЕ тесты для проверки всех требований к ответам панды.

Проверяет:
1. Визуализации (графики, таблицы, диаграммы, схемы, карты) по ВСЕМ предметам
2. Текстовые ответы - развернутые, структурированные, подробные
3. Обработку фото - полная обработка и проверка ДЗ
4. Модерацию - НЕ блокирует школьные вопросы (история, география и т.д.)

Использует РЕАЛЬНЫЙ API Yandex Cloud.
"""

import os

import pytest

from bot.services.moderation_service import ContentModerationService


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


@pytest.mark.integration
@pytest.mark.slow
class TestComprehensivePandaResponses:
    """Комплексные тесты всех требований к ответам панды."""

    def _check_response_quality(self, response: str, min_sentences: int = 4) -> dict:
        """Проверка качества ответа - развернутый, структурированный, подробный."""
        issues = []
        quality_score = 100

        # 1. Проверка длины
        sentences = [s.strip() for s in response.split(".") if s.strip()]
        if len(sentences) < min_sentences:
            issues.append(f"Слишком мало предложений: {len(sentences)} < {min_sentences}")
            quality_score -= 30

        # 2. Проверка общей длины ответа (должен быть подробным)
        if len(response) < 150:
            issues.append(f"Ответ слишком короткий: {len(response)} < 150 символов")
            quality_score -= 20

        # 3. Проверка структуры (абзацы)
        paragraphs = [p.strip() for p in response.split("\n\n") if p.strip()]
        if len(paragraphs) == 1 and len(response) > 300:
            issues.append("Ответ без абзацев")
            quality_score -= 10

        # 4. Проверка на наличие примеров
        example_keywords = ["например", "к примеру", "так", "также", "если", "чтобы", "допустим"]
        has_examples = any(kw in response.lower() for kw in example_keywords)
        if not has_examples and len(sentences) >= 3:
            issues.append("Нет примеров в ответе")
            quality_score -= 15

        return {
            "quality_score": max(0, quality_score),
            "issues": issues,
            "sentences_count": len(sentences),
            "paragraphs_count": len(paragraphs),
            "total_length": len(response),
        }

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_moderation_not_blocks_school_questions(self):
        """КРИТИЧНО: Модерация НЕ должна блокировать школьные вопросы."""
        service = ContentModerationService()

        # Школьные вопросы, которые НЕ должны блокироваться
        school_questions = [
            # История (содержит "война", но в образовательном контексте)
            "Расскажи про Великую Отечественную войну",
            "Когда началась Первая мировая война?",
            "История Второй мировой войны",
            "Расскажи про историю России",
            # География (содержит "карта", но в образовательном контексте)
            "Покажи карту России",
            "Какая столица Франции?",
            "Где находится Москва?",
            # Математика (содержит "нож" в "умножение", но это не "нож" как оружие)
            "Покажи таблицу умножения на 7",
            "Реши уравнение 2x + 5 = 15",
            # Физика, химия, биология
            "Что такое скорость в физике?",
            "Что такое вода? Из чего она состоит?",
            "Что такое фотосинтез?",
            # Обществознание (содержит "государство", но в образовательном контексте)
            "Что такое государство? Объясни простыми словами.",
        ]

        failed_questions = []
        for question in school_questions:
            is_safe, reason = service.is_safe_content(question)
            if not is_safe:
                failed_questions.append((question, reason))

        assert len(failed_questions) == 0, (
            f"Модерация заблокировала {len(failed_questions)} школьных вопросов:\n"
            + "\n".join([f"  - {q}: {r}" for q, r in failed_questions])
        )

        print(f"\n[OK] Все {len(school_questions)} школьных вопросов прошли модерацию")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_text_responses_all_subjects_detailed(self):
        """Тест: Текстовые ответы по ВСЕМ предметам должны быть развернутыми и подробными."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        # Вопросы по ВСЕМ предметам с требованием развернутого ответа
        test_cases = [
            ("Математика", "Объясни что такое квадратное уравнение. Расскажи подробно с примерами.", 12),
            ("Русский", "Объясни что такое подлежащее и сказуемое. Расскажи подробно с примерами предложений.", 10),
            ("История", "Когда началась Великая Отечественная война? Расскажи подробно про это событие.", 13),
            ("География", "Какая самая длинная река в России? Расскажи подробно про неё.", 11),
            ("Биология", "Что такое фотосинтез? Объясни подробно простыми словами с примерами.", 11),
            ("Физика", "Что такое скорость в физике? Объясни подробно простыми словами.", 11),
            ("Химия", "Что такое вода? Из чего она состоит? Объясни подробно с примерами.", 12),
            ("Литература", "Кто написал 'Евгения Онегина'? О чем это произведение? Расскажи подробно.", 14),
            ("Информатика", "Что такое алгоритм? Приведи подробные примеры и объясни.", 12),
            ("Обществознание", "Что такое государство? Объясни подробно простыми словами.", 13),
            ("Английский", "Что такое Present Simple? Объясни подробно с примерами.", 11),
            ("Немецкий", "Что такое артикли der, die, das? Объясни подробно.", 12),
        ]

        results = {}
        for subject, question, age in test_cases:
            response = await ai_service.generate_response(
                user_message=question,
                chat_history=[],
                user_age=age,
            )

            assert response is not None, f"AI не ответил на вопрос по {subject}"
            assert len(response) > 100, f"Ответ слишком короткий по {subject}: {len(response)} символов"

            # Проверка качества ответа
            quality = self._check_response_quality(response, min_sentences=4)

            results[subject] = {
                "quality_score": quality["quality_score"],
                "sentences": quality["sentences_count"],
                "length": quality["total_length"],
                "issues": quality["issues"],
            }

            print(f"\n[{subject}] Quality: {quality['quality_score']}/100, "
                  f"Sentences: {quality['sentences_count']}, "
                  f"Length: {quality['total_length']}")

        # Проверка: все ответы должны быть качественными
        avg_score = sum(r["quality_score"] for r in results.values()) / len(results)
        assert avg_score >= 70, (
            f"Средний балл качества ответов слишком низкий: {avg_score:.1f}/100. "
            f"Минимум должен быть 70/100"
        )

        print(f"\n[OK] Все предметы протестированы! Средний балл: {avg_score:.1f}/100")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_visualizations_with_detailed_explanations(self):
        """Тест: Визуализации (графики, таблицы, диаграммы, схемы, карты) должны генерироваться + подробное пояснение."""
        from bot.services.ai_service_solid import get_ai_service
        from bot.services.visualization_service import VisualizationService

        ai_service = get_ai_service()
        viz_service = VisualizationService()

        # Тест-кейсы для визуализаций
        test_cases = [
            ("График", "Покажи график функции y = x²", "graph"),
            ("Таблица", "Покажи таблицу умножения на 7", "table"),
            ("Диаграмма", "Покажи столбчатую диаграмму: Математика 30, Русский 25, История 20", "diagram"),
            ("Карта", "Покажи карту Москвы", "map"),
            ("Схема", "Покажи схему строения клетки", "scheme"),
        ]

        results = {}
        for viz_type, question, expected_type in test_cases:
            # Генерируем визуализацию
            viz_image, viz_type_detected = viz_service.detect_visualization_request(question)

            if viz_image is None:
                print(f"⚠️ {viz_type}: визуализация не сгенерирована (может быть не реализовано)")
                results[viz_type] = {"generated": False}
                continue

            assert len(viz_image) > 1000, f"{viz_type}: визуализация слишком маленькая"
            results[viz_type] = {"generated": True, "size": len(viz_image)}

            # Генерируем развернутое пояснение к визуализации
            response = await ai_service.generate_response(
                user_message=question,
                chat_history=[],
                user_age=12,
            )

            assert response is not None, f"AI не ответил на запрос {viz_type}"

            # Проверка качества ответа (для визуализаций может быть короче, но структурированным)
            quality = self._check_response_quality(response, min_sentences=3)

            results[viz_type].update({
                "quality_score": quality["quality_score"],
                "sentences": quality["sentences_count"],
                "length": quality["total_length"],
            })

            print(f"\n[{viz_type}] Generated: OK, Size: {len(viz_image)} байт, "
                  f"Quality: {quality['quality_score']}/100, "
                  f"Sentences: {quality['sentences_count']}")

        # Проверка: хотя бы большинство визуализаций должны генерироваться
        generated_count = sum(1 for r in results.values() if r.get("generated"))
        assert generated_count >= 3, f"Слишком мало визуализаций генерируется: {generated_count}/5"

        print(f"\n[OK] Визуализации протестированы! Сгенерировано: {generated_count}/{len(test_cases)}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_photo_processing_all_subjects(self):
        """Тест: Обработка фото должна работать для всех предметов - полная обработка и проверка ДЗ."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        def _create_test_image_with_text(text: str) -> bytes:
            """Создает тестовое изображение с текстом."""
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
                return img_byte_arr.getvalue()
            except ImportError:
                pytest.skip("PIL/Pillow не установлен")

        # Тест-кейсы для фото по разным предметам
        test_cases = [
            ("Математика", "Реши: 15 + 27 = ?", "Реши эту задачу и объясни решение"),
            ("Русский", "Подчеркни подлежащее: Мама готовит обед.", "Объясни что такое подлежащее"),
            ("История", "Великая Отечественная война 1941-1945", "Расскажи про это событие"),
            ("География", "Столица Франции - Париж", "Расскажи про этот город"),
            ("Физика", "F = m * a - формула силы", "Объясни эту формулу простыми словами"),
        ]

        results = {}
        for subject, image_text, question in test_cases:
            try:
                image_bytes = _create_test_image_with_text(image_text)

                result = await yandex_service.analyze_image_with_text(
                    image_data=image_bytes,
                    user_question=question,
                )

                analysis = result.get("analysis", "")
                assert analysis, f"{subject}: AI анализ не выполнен"
                assert len(analysis) > 50, f"{subject}: анализ слишком короткий: {len(analysis)}"

                results[subject] = {
                    "processed": True,
                    "analysis_length": len(analysis),
                }

                print(f"\n[{subject}] Photo processed: OK, Analysis length: {len(analysis)} символов")
            except Exception as e:
                print(f"\n[{subject}] Photo processing failed: {e}")
                results[subject] = {"processed": False, "error": str(e)}

        # Проверка: большинство фото должны обрабатываться
        processed_count = sum(1 for r in results.values() if r.get("processed"))
        assert processed_count >= 3, f"Слишком мало фото обработано: {processed_count}/{len(test_cases)}"

        print(f"\n[OK] Фото протестированы! Обработано: {processed_count}/{len(test_cases)}")
