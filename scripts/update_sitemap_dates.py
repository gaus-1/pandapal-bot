#!/usr/bin/env python3
"""
Обновляет lastmod во всех URL в sitemap.xml и dateModified в JSON-LD блоках index.html.
Запуск: python scripts/update_sitemap_dates.py [--date YYYY-MM-DD]
По умолчанию использует сегодняшнюю дату.
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    root = Path(__file__).parent.parent
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Разрешаем передать дату аргументом
    if len(sys.argv) > 2 and sys.argv[1] == "--date":
        today = sys.argv[2]

    # --- sitemap.xml ---
    sitemap_path = root / "frontend" / "public" / "sitemap.xml"
    if sitemap_path.exists():
        content = sitemap_path.read_text(encoding="utf-8")
        updated, count = re.subn(
            r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>",
            f"<lastmod>{today}</lastmod>",
            content,
        )
        sitemap_path.write_text(updated, encoding="utf-8")
        print(f"sitemap.xml: обновлено {count} lastmod -> {today}")
    else:
        print("sitemap.xml: не найден")

    # --- index.html (JSON-LD dateModified) ---
    index_path = root / "frontend" / "index.html"
    if index_path.exists():
        content = index_path.read_text(encoding="utf-8")
        updated, count = re.subn(
            r'"dateModified":\s*"\d{4}-\d{2}-\d{2}"',
            f'"dateModified": "{today}"',
            content,
        )
        index_path.write_text(updated, encoding="utf-8")
        print(f"index.html: обновлено {count} dateModified -> {today}")
    else:
        print("index.html: не найден")


if __name__ == "__main__":
    main()
