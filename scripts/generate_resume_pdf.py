#!/usr/bin/env python3
"""
Скрипт для автоматической генерации PDF из резюме.

Использование:
    python scripts/generate_resume_pdf.py

Требования:
    pip install weasyprint markdown-it-py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from markdown_it import MarkdownIt
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    try:
        from markdown_it import MarkdownIt
        MARKDOWN_AVAILABLE = True
    except ImportError:
        MARKDOWN_AVAILABLE = False
        print("[ERROR] Необходимо установить: pip install markdown-it-py weasyprint")
        sys.exit(1)


def markdown_to_html(markdown_content: str) -> str:
    """Конвертировать Markdown в HTML."""
    md = MarkdownIt("gfm-like").enable(["table", "strikethrough"])
    md.options["linkify"] = False
    html_body = md.render(markdown_content)

    html_template = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Савин Вячеслав Евгеньевич — Backend Developer</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
            @top-center {{
                content: "Савин Вячеслав Евгеньевич — Backend Developer";
                font-size: 9pt;
                color: #666;
            }}
            @bottom-center {{
                content: "Страница " counter(page) " из " counter(pages);
                font-size: 9pt;
                color: #666;
            }}
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            font-size: 11pt;
            max-width: 210mm;
            margin: 0 auto;
            padding: 20px;
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 24pt;
            page-break-after: avoid;
        }}
        
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 8px;
            margin-top: 25px;
            margin-bottom: 15px;
            font-size: 16pt;
            page-break-after: avoid;
        }}
        
        h3 {{
            color: #555;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 13pt;
            page-break-after: avoid;
        }}
        
        h4 {{
            color: #666;
            margin-top: 15px;
            margin-bottom: 8px;
            font-size: 12pt;
        }}
        
        p {{
            margin: 8px 0;
        }}
        
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 10pt;
            color: #e83e8c;
        }}
        
        pre {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            overflow-x: auto;
            page-break-inside: avoid;
            font-size: 9pt;
            line-height: 1.4;
        }}
        
        pre code {{
            background-color: transparent;
            padding: 0;
            color: #333;
        }}
        
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        
        li {{
            margin: 5px 0;
            page-break-inside: avoid;
        }}
        
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #e9ecef;
            margin: 30px 0;
            page-break-after: avoid;
        }}
        
        strong {{
            color: #2c3e50;
            font-weight: 600;
        }}
        
        .contact-info {{
            margin: 10px 0;
            font-size: 10pt;
            color: #555;
        }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>
    """
    return html_template


def generate_pdf():
    """Генерация PDF из Markdown файла резюме."""
    markdown_file = project_root / "RESUME_SAVIN_VYACHESLAV.md"
    output_pdf = project_root / "RESUME_SAVIN_VYACHESLAV.pdf"

    if not markdown_file.exists():
        print(f"[ERROR] Файл не найден: {markdown_file}")
        sys.exit(1)

    if not WEASYPRINT_AVAILABLE:
        print("[WARNING] weasyprint не установлен. Генерирую HTML вместо PDF...")
        print("[INFO] Для генерации PDF установите: pip install weasyprint")
        generate_html()
        return

    print(f"[INFO] Чтение файла: {markdown_file}")
    markdown_content = markdown_file.read_text(encoding="utf-8")

    print("[INFO] Конвертация Markdown -> HTML...")
    html_content = markdown_to_html(markdown_content)

    print("[INFO] Генерация PDF...")
    try:
        HTML(string=html_content).write_pdf(
            output_pdf,
            stylesheets=[
                CSS(string="""
                    @page {
                        size: A4;
                        margin: 2cm;
                    }
                """)
            ],
        )
        print(f"[SUCCESS] PDF успешно создан: {output_pdf}")
        print(f"[INFO] Размер файла: {output_pdf.stat().st_size / 1024:.1f} KB")
    except Exception as e:
        print(f"[ERROR] Ошибка генерации PDF: {e}")
        print("\n[INFO] Альтернативный вариант:")
        print("   1. Установите weasyprint: pip install weasyprint")
        print("   2. Или откройте RESUME_SAVIN_VYACHESLAV.html в браузере и сохраните как PDF")
        generate_html()


def generate_html():
    """Генерация HTML из Markdown файла резюме (fallback)."""
    markdown_file = project_root / "RESUME_SAVIN_VYACHESLAV.md"
    output_html = project_root / "RESUME_SAVIN_VYACHESLAV.html"

    if not markdown_file.exists():
        print(f"[ERROR] Файл не найден: {markdown_file}")
        sys.exit(1)

    print(f"[INFO] Чтение файла: {markdown_file}")
    markdown_content = markdown_file.read_text(encoding="utf-8")

    print("[INFO] Конвертация Markdown -> HTML...")
    html_content = markdown_to_html(markdown_content)

    output_html.write_text(html_content, encoding="utf-8")
    print(f"[SUCCESS] HTML файл создан: {output_html}")
    print(f"[INFO] Откройте файл в браузере и используйте 'Печать -> Сохранить как PDF'")


if __name__ == "__main__":
    generate_pdf()
