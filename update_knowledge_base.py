"""
Скрипт для ручного обновления базы знаний.

Используется для еженедельного обновления образовательных материалов.
Можно запускать через cron/планировщик задач Windows.

Пример:
    python update_knowledge_base.py
"""
import asyncio
import sys
from pathlib import Path

from loguru import logger

from bot.services.knowledge_service import get_knowledge_service

# Добавляем корень проекта в sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def main():
    """Обновить базу знаний."""
    logger.info("=" * 60)
    logger.info("🔄 ОБНОВЛЕНИЕ БАЗЫ ЗНАНИЙ")
    logger.info("=" * 60)

    try:
        # Получаем сервис знаний
        knowledge_service = get_knowledge_service()

        # Включаем авто-обновление на время выполнения
        knowledge_service.auto_update_enabled = True

        # Обновляем базу знаний
        await knowledge_service.update_knowledge_base()

        # Получаем статистику
        stats = knowledge_service.get_knowledge_stats()

        logger.info("\n📊 СТАТИСТИКА:")
        logger.info(f"Всего предметов: {len(stats)}")
        for subject, count in stats.items():
            logger.info(f"  • {subject}: {count} материалов")

        logger.info("\n✅ Обновление завершено успешно!")

    except Exception as e:
        logger.error(f"❌ Ошибка обновления: {e}")
        sys.exit(1)

    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
