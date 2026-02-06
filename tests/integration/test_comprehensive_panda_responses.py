"""
КОМПЛЕКСНЫЕ тесты для проверки всех требований к ответам панды.

Проверяет:
1. Визуализации (графики, таблицы, диаграммы, схемы, карты) по ВСЕМ предметам
2. Текстовые ответы - развернутые, структурированные, подробные
3. Запросы «подробнее», «объясни», «приведи примеры для закрепления» — структура и грамотность
4. Обработку фото - полная обработка и проверка ДЗ
5. Модерацию - НЕ блокирует школьные вопросы (история, география и т.д.)

Использует РЕАЛЬНЫЙ API Yandex Cloud.
"""

import os
import re

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

    def _assert_structure_and_russian(self, response: str, context: str = "") -> None:
        """
        Строгая проверка: структура (абзацы, списки/жирный) и грамотность (законченные предложения).
        Промпт: СТРУКТУРА ОТВЕТА, ОТВЕТ НА «ПОДРОБНЕЕ», ГРАМОТНОСТЬ, ПРАВИЛА ПОСТРОЕНИЯ ТЕКСТА.
        """
        assert response and len(response.strip()) > 50, (
            f"{context}Ответ слишком короткий или пустой"
        )
        paragraphs = [p.strip() for p in response.split("\n\n") if p.strip()]
        # Длинный ответ — обязательно абзацы (запрещён сплошной текст)
        if len(response) > 250:
            assert len(paragraphs) >= 2, (
                f"{context}Ответ без абзацев (должны быть \\n\\n между блоками). "
                f"Получено абзацев: {len(paragraphs)}"
            )
        # Маркеры структуры: списки (- или 1. 2. 3.) или жирный (**термин**)
        has_lists = "- " in response or "\n- " in response or re.search(r"\n\d+\.\s", response)
        has_bold = "**" in response
        assert has_lists or has_bold, (
            f"{context}Нет списков (- или 1. 2. 3.) или выделений (**). "
            "Промпт требует структурированный ответ."
        )
        # Грамотность: предложения должны заканчиваться точкой/вопросом/восклицанием
        sentence_endings = response.count(".") + response.count("!") + response.count("?")
        assert sentence_endings >= 2, (
            f"{context}Мало законченных предложений (нужны . ! ?). Получено: {sentence_endings}"
        )
        # Нет склеенных слов (артефакты модели)
        assert "УПривет" not in response and "шеПривет" not in response, (
            f"{context}Склеенные слова в ответе (УПривет, шеПривет и т.п.)"
        )

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

    def test_meta_question_about_limits_allowed(self):
        """Мета-вопросы «что тебе запрещено» не блокируются — Панда на них отвечает."""
        service = ContentModerationService()
        meta_questions = [
            "Что тебе запрещено обсуждать?",
            "О чём ты не говоришь?",
            "Какие у тебя ограничения?",
            "Что ты не обсуждаешь?",
            "Что тебе нельзя говорить?",
        ]
        for text in meta_questions:
            is_safe, reason = service.is_safe_content(text)
            assert is_safe, f"Мета-вопрос не должен блокироваться: {text!r} (reason={reason})"
        print(f"\n[OK] Все {len(meta_questions)} мета-вопросов разрешены")

    def test_blocked_profanity_gets_redirect_not_silence(self):
        """При блоке за мат пользователь получает вежливый перевод темы, не молчание."""
        service = ContentModerationService()
        is_safe, _ = service.is_safe_content("What the fuck is this?")
        assert not is_safe, "Профанити должен блокироваться"
        redirect = service.get_safe_response_alternative("ненормативная лексика")
        assert redirect and len(redirect.strip()) > 20, (
            "При блоке должен быть вежливый редирект, не пусто"
        )
        redirect_lower = redirect.lower()
        assert (
            "учёб" in redirect_lower
            or "учеб" in redirect_lower
            or "школ" in redirect_lower
            or "помощ" in redirect_lower
            or "помог" in redirect_lower
        ), "Редирект должен предлагать учёбу/помощь"
        print(f"\n[OK] Редирект при блоке: {redirect[:80]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_meta_question_what_forbidden_gets_answer(self):
        """Мета-вопрос «что тебе запрещено» — Панда отвечает вежливо, не молчит."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()
        question = "Что тебе запрещено обсуждать? О чём ты не говоришь?"
        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=12,
        )
        assert response is not None, "Панда должна ответить на мета-вопрос"
        assert len(response.strip()) > 30, "Ответ не должен быть пустым или односложным"
        assert (
            "учёб" in response.lower()
            or "школ" in response.lower()
            or "помощ" in response.lower()
            or "предмет" in response.lower()
        ), "Ответ должен вежливо переводить на учёбу"
        print(f"\n[OK] Мета-вопрос получил ответ: {response[:120]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_podrobnee_followup_has_structure(self):
        """ОТВЕТ НА «ПОДРОБНЕЕ»: при follow-up «Подробнее» ответ обязан быть структурирован (абзацы, списки, **)."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()
        chat_history = [
            {"role": "user", "text": "Что такое парабола?"},
            {
                "role": "assistant",
                "text": "Парабола — это график квадратичной функции y = x². Она симметрична и имеет вершину.",
            },
            {"role": "user", "text": "Расскажи подробнее"},
        ]
        response = await ai_service.generate_response(
            user_message="Расскажи подробнее",
            chat_history=chat_history,
            user_age=12,
        )
        self._assert_structure_and_russian(response, context="[Подробнее] ")
        print(f"\n[OK] Подробнее (follow-up): структура соблюдена, ответ: {len(response)} символов")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_examples_for_reinforcement_has_structure(self):
        """При запросе «примеры для закрепления» / «задачи на закрепление» — структура обязательна (промпт ПОЛНОТА)."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()
        response = await ai_service.generate_response(
            user_message="Приведи примеры для закрепления по теме квадратные уравнения. Задачи с пояснением.",
            chat_history=[],
            user_age=14,
        )
        self._assert_structure_and_russian(response, context="[Примеры для закрепления] ")
        print(
            f"\n[OK] Примеры для закрепления: структура соблюдена, ответ: {len(response)} символов"
        )

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_obyasni_privesti_primeri_has_structure(self):
        """Запросы «Объясни» / «приведи примеры» — структура и грамотность (русский язык)."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()
        response = await ai_service.generate_response(
            user_message="Объясни что такое подлежащее и сказуемое. Приведи примеры предложений для закрепления.",
            chat_history=[],
            user_age=10,
        )
        self._assert_structure_and_russian(response, context="[Объясни + примеры] ")
        print(
            f"\n[OK] Объясни + примеры: структура и грамотность соблюдены, ответ: {len(response)} символов"
        )

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_obyasni_podrobnee_first_message_has_structure(self):
        """Первый запрос «Объясни подробнее про X» — структура обязательна (триггеры промпта ОТВЕТ НА «ПОДРОБНЕЕ»)."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()
        response = await ai_service.generate_response(
            user_message="Объясни подробнее про фотосинтез: как происходит, зачем нужен растениям.",
            chat_history=[],
            user_age=11,
        )
        self._assert_structure_and_russian(response, context="[Объясни подробнее] ")
        print(
            f"\n[OK] Объясни подробнее (первый запрос): структура соблюдена, ответ: {len(response)} символов"
        )

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_text_responses_all_subjects_detailed(self):
        """Тест: Текстовые ответы по ВСЕМ предметам должны быть развернутыми и подробными."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

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
            (
                "Литература",
                "Кто написал 'Евгения Онегина'? О чем это произведение? Расскажи подробно.",
                14,
            ),
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
            assert len(response) > 100, (
                f"Ответ слишком короткий по {subject}: {len(response)} символов"
            )

            # Проверка качества ответа
            quality = self._check_response_quality(response, min_sentences=4)

            results[subject] = {
                "quality_score": quality["quality_score"],
                "sentences": quality["sentences_count"],
                "length": quality["total_length"],
                "issues": quality["issues"],
            }

            print(
                f"\n[{subject}] Quality: {quality['quality_score']}/100, "
                f"Sentences: {quality['sentences_count']}, "
                f"Length: {quality['total_length']}"
            )

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
            (
                "Диаграмма",
                "Покажи столбчатую диаграмму: Математика 30, Русский 25, История 20",
                "diagram",
            ),
            ("Карта", "Покажи карту Москвы", "map"),
            ("Схема", "Покажи схему строения клетки", "scheme"),
        ]

        results = {}
        for viz_type, question, expected_type in test_cases:
            # Генерируем визуализацию
            viz_image, viz_type_detected = viz_service.detect_visualization_request(question)

            if viz_image is None:
                print(
                    f"[WARNING] {viz_type}: визуализация не сгенерирована (может быть не реализовано)"
                )
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

            results[viz_type].update(
                {
                    "quality_score": quality["quality_score"],
                    "sentences": quality["sentences_count"],
                    "length": quality["total_length"],
                }
            )

            print(
                f"\n[{viz_type}] Generated: OK, Size: {len(viz_image)} байт, "
                f"Quality: {quality['quality_score']}/100, "
                f"Sentences: {quality['sentences_count']}"
            )

        # Проверка: хотя бы большинство визуализаций должны генерироваться
        generated_count = sum(1 for r in results.values() if r.get("generated"))
        assert generated_count >= 3, f"Слишком мало визуализаций генерируется: {generated_count}/5"

        print(
            f"\n[OK] Визуализации протестированы! Сгенерировано: {generated_count}/{len(test_cases)}"
        )

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

                print(
                    f"\n[{subject}] Photo processed: OK, Analysis length: {len(analysis)} символов"
                )
            except Exception as e:
                print(f"\n[{subject}] Photo processing failed: {e}")
                results[subject] = {"processed": False, "error": str(e)}

        # Проверка: большинство фото должны обрабатываться
        processed_count = sum(1 for r in results.values() if r.get("processed"))
        assert processed_count >= 3, (
            f"Слишком мало фото обработано: {processed_count}/{len(test_cases)}"
        )

        print(f"\n[OK] Фото протестированы! Обработано: {processed_count}/{len(test_cases)}")
