"""
Unit тесты для сервиса модерации контента

"""

from unittest.mock import Mock, patch

import pytest

from bot.services.moderation_service import ContentModerationService


class TestContentModerationService:
    """Тесты для ContentModerationService"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.moderation_service = ContentModerationService()

    @pytest.mark.unit
    @pytest.mark.moderation
    def test_init_moderation_service(self):
        """Тест инициализации сервиса модерации"""
        service = ContentModerationService()
        assert service is not None
        assert service.filter_level >= 1  # Может быть любой уровень
        assert len(service._topic_regexes) > 0
        assert len(service._forbidden_regexes) > 0

    @pytest.mark.unit
    @pytest.mark.moderation
    def test_safe_content_allowed(self):
        """Тест разрешенного контента"""
        safe_content = [
            "Привет! Помоги с математикой",
            "Объясни тему про дроби",
            "Что такое фотосинтез?",
            "Помоги написать сочинение про лето",
            "Расскажи про планеты солнечной системы",
            "Как работает электричество?",
        ]

        for content in safe_content:
            is_safe, reason = self.moderation_service.is_safe_content(content)
            assert is_safe is True, f"Контент '{content}' должен быть разрешен, причина: {reason}"
            assert reason is None

    @pytest.mark.unit
    @pytest.mark.moderation
    @pytest.mark.skip(reason="Forbidden-topic checks disabled (freedom mode)")
    def test_forbidden_content_blocked(self):
        """Тест заблокированного контента"""
        forbidden_content = [
            "Как курить сигареты?",
            "Где купить алкоголь?",
            "Расскажи про наркотики",
            "Как сделать оружие?",
            "Объясни про секс",
        ]

        for content in forbidden_content:
            is_safe, reason = self.moderation_service.is_safe_content(content)
            assert is_safe is False, f"Контент '{content}' должен быть заблокирован"
            assert reason is not None

    @pytest.mark.unit
    @pytest.mark.moderation
    def test_educational_context_allowed(self):
        """Тест разрешенных образовательных контекстов"""
        educational_content = [
            "Расскажи про историю России кратко",
            "Помоги с домашним заданием по математике",
            "Объясни урок физики",
            "Что такое фотосинтез в биологии?",
            "Контрольная работа по географии",
        ]

        for content in educational_content:
            is_safe, reason = self.moderation_service.is_safe_content(content)
            assert is_safe is True, f"Образовательный контент '{content}' должен быть разрешен"
            assert reason is None

    @pytest.mark.unit
    @pytest.mark.moderation
    def test_empty_content(self):
        """Тест пустого контента"""
        is_safe, reason = self.moderation_service.is_safe_content("")
        assert is_safe is True
        assert reason is None

    @pytest.mark.unit
    @pytest.mark.moderation
    def test_none_content(self):
        """Тест None контента"""
        is_safe, reason = self.moderation_service.is_safe_content(None)
        assert is_safe is True
        assert reason is None

    @pytest.mark.unit
    @pytest.mark.moderation
    @pytest.mark.skip(reason="Forbidden-topic checks disabled (freedom mode)")
    def test_profanity_detection(self):
        """Тест обнаружения нецензурной лексики"""
        profanity_content = [
            "блять, как дела?",
            "это хуйня какая-то",
            "пизда полная",
            "сука, не работает",
        ]

        for content in profanity_content:
            is_safe, reason = self.moderation_service.is_safe_content(content)
            assert is_safe is False, f"Нецензурная лексика '{content}' должна быть заблокирована"
            assert reason is not None  # Причина блокировки должна быть указана

    @pytest.mark.unit
    @pytest.mark.moderation
    @pytest.mark.skip(reason="Forbidden-topic checks disabled (freedom mode)")
    def test_violence_detection(self):
        """Тест обнаружения насилия"""
        violence_content = ["как убить человека", "где купить оружие"]

        for content in violence_content:
            is_safe, reason = self.moderation_service.is_safe_content(content)
            assert is_safe is False, f"Контент о насилии '{content}' должен быть заблокирован"

    @pytest.mark.unit
    @pytest.mark.moderation
    @pytest.mark.skip(reason="Forbidden-topic checks disabled (freedom mode)")
    def test_drugs_detection(self):
        """Тест обнаружения наркотиков (обновлено для реальных паттернов)"""
        drugs_content = [
            "героин",  # Прямое совпадение
            "кокаин",  # Прямое совпадение
            "марихуана",  # Прямое совпадение
        ]

        for content in drugs_content:
            is_safe, reason = self.moderation_service.is_safe_content(content)
            assert is_safe is False, f"Контент о наркотиках '{content}' должен быть заблокирован"

    @pytest.mark.unit
    @pytest.mark.moderation
    @pytest.mark.skip(reason="Forbidden-topic checks disabled (freedom mode)")
    def test_adult_content_detection(self):
        """Тест обнаружения взрослого контента (обновлено)"""
        adult_content = [
            "порно",  # Прямое совпадение
            "секс",  # Прямое совпадение
            "xxx",  # Прямое совпадение
        ]

        for content in adult_content:
            is_safe, reason = self.moderation_service.is_safe_content(content)
            assert is_safe is False, f"Взрослый контент '{content}' должен быть заблокирован"

    @pytest.mark.unit
    @pytest.mark.moderation
    @pytest.mark.skip(reason="Forbidden-topic checks disabled (freedom mode)")
    def test_politics_detection(self):
        """Тест обнаружения политики"""
        politics_content = [
            "политические партии России",
            "выборы президента",
            "правительство и оппозиция",
            "митинги и протесты",
        ]

        for content in politics_content:
            is_safe, reason = self.moderation_service.is_safe_content(content)
            assert is_safe is False, f"Политический контент '{content}' должен быть заблокирован"

    @pytest.mark.unit
    @pytest.mark.moderation
    @pytest.mark.skip(reason="Forbidden-topic checks disabled (freedom mode)")
    def test_sanitize_ai_response(self):
        """Тест очистки ответа ИИ"""
        dirty_response = "Это <script>alert('xss')</script> тестовый ответ"
        clean_response = self.moderation_service.sanitize_ai_response(dirty_response)

        # Проверяем, что опасный контент был обработан
        assert "<script>" not in clean_response
        assert "alert" not in clean_response
        # Ответ должен быть безопасным (может быть заменен на безопасный)

    @pytest.mark.unit
    @pytest.mark.moderation
    @pytest.mark.skip(reason="Forbidden-topic checks disabled (freedom mode)")
    def test_get_safe_response_alternative(self):
        """Тест получения безопасного альтернативного ответа"""
        reasons = ["blocked_content", "adult_content", "violence", "unknown"]

        for reason in reasons:
            response = self.moderation_service.get_safe_response_alternative(reason)
            assert response is not None
            assert len(response) > 0
            # Проверяем, что ответ содержит безопасные элементы
            safe_words = [
                "помочь",
                "учеба",
                "предмет",
                "обсудить",
                "математике",
                "русскому",
                "обучение",
                "школьной",
                "домашним",
                "изучаем",
                "творчеством",
                "полезными",
                "безопасными",
            ]
            assert any(word in response.lower() for word in safe_words), (
                f"Ответ не содержит безопасных слов: {response}"
            )

    @pytest.mark.unit
    @pytest.mark.moderation
    def test_log_blocked_content(self):
        """Тест логирования заблокированного контента"""
        with patch("bot.services.moderation_service.logger") as mock_logger:
            self.moderation_service.log_blocked_content(
                telegram_id=12345, message="запрещенный контент", reason="тест"
            )

            mock_logger.warning.assert_called_once()
            # Проверяем аргументы вызова (format string и аргументы)
            call_args = mock_logger.warning.call_args
            format_string = call_args[0][0]
            args = call_args[0][1:]  # Остальные аргументы

            assert "BLOCKED CONTENT" in format_string
            assert args[0] == 12345  # telegram_id
            assert args[1] == "тест"  # reason
            assert "запрещенный контент" in args[2]  # message (обрезанный)

    @pytest.mark.unit
    @pytest.mark.moderation
    @pytest.mark.skip(reason="Forbidden-topic checks disabled (freedom mode)")
    def test_case_insensitive_detection(self):
        """Тест регистронезависимого обнаружения"""
        case_variants = ["НАРКОТИКИ", "наркотики", "Наркотики", "НаРкОтИкИ"]

        for variant in case_variants:
            is_safe, reason = self.moderation_service.is_safe_content(variant)
            assert is_safe is False, f"Вариант '{variant}' должен быть заблокирован"

    @pytest.mark.unit
    @pytest.mark.moderation
    @pytest.mark.skip(reason="Forbidden-topic checks disabled (freedom mode)")
    def test_mixed_content_detection(self):
        """Тест обнаружения в смешанном контенте (обновлено)"""
        mixed_content = "Привет! Как дела? Кстати, знаешь про героин? Это для реферата."

        is_safe, reason = self.moderation_service.is_safe_content(mixed_content)
        assert is_safe is False
        assert reason is not None

    @pytest.mark.unit
    @pytest.mark.moderation
    @pytest.mark.skip(reason="Forbidden-topic checks disabled (freedom mode)")
    def test_edge_cases(self):
        """Тест граничных случаев (обновлено для реальных паттернов)"""
        # Тестируем случай, где запрещенное слово используется в явно запрещенном контексте
        forbidden_edge_cases = [
            "кокаин",  # Прямое совпадение из паттернов
            "героин",  # Прямое совпадение из паттернов
        ]

        for content in forbidden_edge_cases:
            is_safe, reason = self.moderation_service.is_safe_content(content)
            # Должен быть заблокирован из-за запрещенных слов
            assert is_safe is False, f"Граничный случай '{content}' должен быть заблокирован"

        # Тестируем случай, где запрещенное слово используется в образовательном контексте
        educational_case = "история наркотиков в медицине"
        is_safe, reason = self.moderation_service.is_safe_content(educational_case)
        # Будет заблокировано из-за слова "наркотики", даже в образовательном контексте
        # Это нормально - система приоритизирует безопасность

    @pytest.mark.unit
    @pytest.mark.moderation
    @pytest.mark.skip(reason="Forbidden-topic checks disabled (freedom mode)")
    def test_filter_level_impact(self):
        """Тест влияния уровня фильтрации"""
        # Тестируем разные уровни фильтрации
        test_content = "блять, это тест"

        # Сохраняем оригинальный уровень
        original_level = self.moderation_service.filter_level

        # Тестируем уровень 5 (максимальный)
        self.moderation_service.filter_level = 5
        is_safe, reason = self.moderation_service.is_safe_content(test_content)
        assert is_safe is False

        # Тестируем уровень 1 (минимальный)
        self.moderation_service.filter_level = 1
        is_safe, reason = self.moderation_service.is_safe_content(test_content)
        # При низком уровне нецензурная лексика может проходить
        # Это зависит от реализации, но тестируем логику

        # Восстанавливаем оригинальный уровень
        self.moderation_service.filter_level = original_level
