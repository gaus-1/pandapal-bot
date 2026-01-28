"""Модуль визуализации для английского языка."""

from bot.services.visualization.base import BaseVisualizationService


class EnglishVisualization(BaseVisualizationService):
    """Визуализация для английского языка: времена, неправильные глаголы."""

    def generate_english_tenses_table(self) -> bytes | None:
        """Генерирует упрощенную таблицу времен английского языка."""
        headers = ["Время", "Утверждение", "Отрицание", "Вопрос"]
        rows = [
            ["Present Simple", "I work", "I don't work", "Do I work?"],
            ["Past Simple", "I worked", "I didn't work", "Did I work?"],
            ["Future Simple", "I will work", "I won't work", "Will I work?"],
            ["Present Continuous", "I am working", "I'm not working", "Am I working?"],
            ["Past Continuous", "I was working", "I wasn't working", "Was I working?"],
        ]
        return self.generate_table(headers, rows, "Таблица времен английского языка")

    def generate_english_irregular_verbs_table(self) -> bytes | None:
        """Генерирует таблицу неправильных глаголов (топ-20)."""
        headers = ["Infinitive", "Past Simple", "Past Participle", "Перевод"]
        rows = [
            ["be", "was/were", "been", "быть"],
            ["have", "had", "had", "иметь"],
            ["do", "did", "done", "делать"],
            ["go", "went", "gone", "идти"],
            ["see", "saw", "seen", "видеть"],
            ["come", "came", "come", "приходить"],
            ["take", "took", "taken", "брать"],
            ["get", "got", "got/gotten", "получать"],
            ["make", "made", "made", "делать"],
            ["know", "knew", "known", "знать"],
            ["think", "thought", "thought", "думать"],
            ["say", "said", "said", "говорить"],
            ["find", "found", "found", "находить"],
            ["give", "gave", "given", "давать"],
            ["tell", "told", "told", "рассказывать"],
        ]
        return self.generate_table(headers, rows, "Таблица неправильных глаголов")
