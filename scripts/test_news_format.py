#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест форматирования новостей для бота."""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from bot.database import get_db
from bot.services.news.repository import NewsRepository
from bot.keyboards.news_bot.categories_kb import get_category_emoji

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with get_db() as db:
    repo = NewsRepository(db)
    news_list = repo.find_recent(limit=1)

    if not news_list:
        print("Новостей нет в БД")
        sys.exit(1)

    news = news_list[0]
    category_emoji = get_category_emoji(news.category)
    max_content_length = 900

    content = news.content
    if len(content) > max_content_length:
        cut_point = content.rfind(".", 0, max_content_length)
        if cut_point > max_content_length * 0.7:
            content = content[:cut_point + 1] + "\n\n..."
        else:
            cut_point = content.rfind(" ", 0, max_content_length)
            if cut_point > max_content_length * 0.7:
                content = content[:cut_point] + "..."
            else:
                content = content[:max_content_length] + "..."

    text = (
        f"{category_emoji} <b>{news.title}</b>\n"
        f"📂 {news.category.capitalize()}\n\n"
        f"{content}"
    )

    print("=" * 60)
    print("ФОРМАТИРОВАННАЯ НОВОСТЬ ДЛЯ БОТА:")
    print("=" * 60)
    print(text)
    print("=" * 60)
    print(f"\nДлина текста: {len(text)} символов")
    print(f"Есть изображение: {'Да' if news.image_url else 'Нет'}")
    if news.image_url:
        print(f"URL изображения: {news.image_url[:60]}...")
