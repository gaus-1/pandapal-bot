# Presentation - Материалы для презентации

Материалы для презентации проекта PandaPal.

## Файлы

- `pandapal_github_qr.png` - QR-код обычного размера (300x300px) для документов
- `pandapal_github_qr_large.png` - QR-код большого размера (600x600px) для презентаций
- `github_qr_page.html` - интерактивная HTML страница с QR-кодом

## Использование

QR-код ведет на репозиторий проекта: https://github.com/gaus-1/pandapal-bot

### Для презентаций

Вставьте `pandapal_github_qr_large.png` в слайд, добавьте текст "Отсканируйте для просмотра кода".

### Для печати

Используйте `pandapal_github_qr_large.png`, печатайте размером минимум 5x5 см.

### Для веб-демонстрации

Откройте `github_qr_page.html` в браузере, разверните на весь экран.

## Перегенерация QR-кода

Если изменился URL репозитория:

```bash
python scripts/generate_qr_code.py
```
