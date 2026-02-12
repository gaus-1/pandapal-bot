# -*- coding: utf-8 -*-
"""Тесты нормализатора опечаток (примеры, подробнее, температура и т.д.)."""

import pytest

from bot.services.typo_normalizer import normalize_common_typos


def test_normalize_examples_typo():
    """Приперы -> примеры."""
    assert (
        normalize_common_typos("\u043f\u0440\u0438\u043f\u0435\u0440\u044b")
        == "\u043f\u0440\u0438\u043c\u0435\u0440\u044b"
    )


def test_normalize_temperature_typo():
    """Темпереатуры -> температуры."""
    assert (
        normalize_common_typos(
            "\u043d\u0430\u0440\u0438\u0441\u0443\u0439 \u0433\u0440\u0430\u0444\u0438\u043a \u0442\u0435\u043c\u043f\u0435\u0440\u0435\u0430\u0442\u0443\u0440\u044b"
        )
        == "\u043d\u0430\u0440\u0438\u0441\u0443\u0439 \u0433\u0440\u0430\u0444\u0438\u043a \u0442\u0435\u043c\u043f\u0435\u0440\u0430\u0442\u0443\u0440\u044b"
    )


def test_normalize_detail_and_cases():
    """Падежы -> падежи. Подробнее-варианты."""
    assert normalize_common_typos("падежы") == "падежи"


def test_normalize_empty():
    """Пустая строка не меняется."""
    assert normalize_common_typos("") == ""
    assert normalize_common_typos("   ") == "   "


def test_normalize_no_typos():
    """Текст без опечаток не меняется."""
    assert (
        normalize_common_typos("\u043f\u0440\u0438\u043c\u0435\u0440\u044b")
        == "\u043f\u0440\u0438\u043c\u0435\u0440\u044b"
    )
