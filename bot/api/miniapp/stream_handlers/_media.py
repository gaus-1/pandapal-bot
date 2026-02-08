"""Обработка медиа-вложений: аудио и фото."""

from aiohttp import web

from bot.services.miniapp.audio_service import MiniappAudioService
from bot.services.miniapp.photo_service import MiniappPhotoService


async def process_media(
    audio_base64: str | None,
    photo_base64: str | None,
    telegram_id: int,
    message: str,
    response: web.StreamResponse,
    language_code: str | None = None,
) -> str | None:
    """Обработка аудио/фото. Возвращает user_message или None (ошибка/завершено)."""
    user_message = message

    if audio_base64:
        audio_service = MiniappAudioService()
        user_message = await audio_service.process_audio(
            audio_base64, telegram_id, response, language_code=language_code
        )
        if user_message is None:
            return None

    if photo_base64:
        photo_service = MiniappPhotoService()
        user_message, is_completed = await photo_service.process_photo(
            photo_base64, telegram_id, message, response
        )
        if is_completed:
            return None

    if not user_message or not user_message.strip():
        await response.write(
            b'event: error\ndata: {"error": "message, photo or audio required"}\n\n'
        )
        return None

    return user_message
