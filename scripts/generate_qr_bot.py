"""
Генерация статического QR-кода для лендинга (бот PandaPal).
Сохраняет PNG в frontend/public/qr-bot.png. Запускать при смене URL бота.
"""
from pathlib import Path

import qrcode

# URL бота — при смене домена/бота обновить и перезапустить скрипт
BOT_URL = "https://t.me/PandaPalBot"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "frontend" / "public" / "qr-bot.png"
def main() -> None:
    # box_size 8, border 4 → ~232px, достаточно для сканирования
    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
    )
    qr.add_data(BOT_URL)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT_PATH, "PNG")
    print(f"QR сохранён: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
