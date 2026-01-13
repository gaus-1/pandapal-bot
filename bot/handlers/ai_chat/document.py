"""
Обработка документов для AI чата.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.monitoring import log_user_activity, monitor_performance


def register_handlers(router: Router) -> None:
    """Регистрирует handlers для документов."""
    router.message.register(handle_document, F.document)


@monitor_performance
async def handle_document(message: Message, state: FSMContext):  # noqa: ARG001
    """
    Обработка документов (PDF, Word и т.д.)

    Args:
        message: Сообщение с документом
        state: FSM состояние
    """
    try:
        # Проверяем тип документа
        document = message.document

        # Поддерживаемые форматы
        supported_formats = {
            "application/pdf": "PDF",
            "application/msword": "Word",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word",
            "text/plain": "Текстовый файл",
        }

        file_type = supported_formats.get(document.mime_type, "Неизвестный формат")

        # Проверяем размер файла (максимум 20MB)
        if document.file_size > 20 * 1024 * 1024:
            await message.answer(
                "📄 Файл слишком большой! Максимум 20MB. "
                "Попробуй сжать документ или скопировать текст 📏"
            )
            return

        # Показываем информацию о файле
        await message.answer(
            f"📄 Получен документ: {document.file_name}\n"
            f"Тип: {file_type}\n"
            f"Размер: {document.file_size / 1024:.1f} KB\n\n"
            "Для полноценной обработки документов нужно больше времени на разработку. "
            "Пока лучше скопируй текст задачи и отправь текстом — я помогу! 📝"
        )

        # Логируем попытку отправки документа
        log_user_activity(
            message.from_user.id,
            "document_upload",
            True,
            f"Type: {file_type}, Size: {document.file_size}",
        )

    except Exception as e:
        logger.error(f"❌ Ошибка обработки документа: {e}")
        await message.answer(
            "📄 Произошла ошибка при обработке документа. " "Попробуй отправить текст задачи! 📝"
        )
        log_user_activity(message.from_user.id, "document_error", False, str(e))
