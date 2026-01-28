#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт для проверки новостей в БД."""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from bot.database import get_db
from bot.services.news.repository import NewsRepository

# Устанавливаем UTF-8 для Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with get_db() as db:
    repo = NewsRepository(db)
    news_list = repo.find_recent(limit=5)

    print(f"Найдено новостей: {len(news_list)}\n")

    for i, news in enumerate(news_list, 1):
        print(f"{i}. {news.category.upper()}: {news.title[:60]}...")
        print(f"   Content: {len(news.content)} символов")
        print(f"   Image: {'Да' if news.image_url else 'Нет'}")
        print()
