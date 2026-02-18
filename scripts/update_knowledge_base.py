"""
Скрипт для ручного обновления базы знаний.

Используется для еженедельного обновления образовательных материалов.
Можно запускать через cron/планировщик задач Windows.
При росте объёма источников целесообразно вынести в воркер/очередь.

1. Скрапит nsportal.ru и school203.spb.ru
2. Индексирует материалы в knowledge_embeddings (pgvector) для семантического поиска

Пример:
    python scripts/update_knowledge_base.py
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from bot.services.knowledge_service import get_knowledge_service


async def main():
    """
    Обновить базу знаний из веб-источников и наполнить knowledge_embeddings.

    Загружает материалы с nsportal.ru и school203.spb.ru,
    индексирует в pgvector для RAG.
    """
    logger.info("=" * 60)
    logger.info("🔄 ОБНОВЛЕНИЕ БАЗЫ ЗНАНИЙ + ИНДЕКСАЦИЯ В knowledge_embeddings")
    logger.info("=" * 60)

    try:
        knowledge_service = get_knowledge_service()
        knowledge_service.auto_update_enabled = True

        await knowledge_service.update_knowledge_base()
        stats = knowledge_service.get_knowledge_stats()

        logger.info("\n📊 Скраплено:")
        for subject, count in stats.items():
            logger.info(f"  • {subject}: {count} материалов")

        # Индексируем в knowledge_embeddings для векторного поиска
        all_materials = []
        for materials in knowledge_service.knowledge_base.values():
            all_materials.extend(materials)

        if all_materials:
            logger.info(f"\n📐 Индексация {len(all_materials)} материалов в knowledge_embeddings...")
            indexed = 0
            for i, material in enumerate(all_materials):
                ok = await knowledge_service.vector_search.index_content(material)
                if ok:
                    indexed += 1
                if (i + 1) % 20 == 0:
                    logger.info(f"  Обработано {i + 1}/{len(all_materials)}")
            logger.info(f"  ✅ Проиндексировано: {indexed}/{len(all_materials)}")
        else:
            logger.warning("  Нет материалов для индексации")

        logger.info("\n✅ Обновление завершено успешно!")

    except Exception as e:
        logger.error(f"❌ Ошибка обновления: {e}")
        sys.exit(1)

    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
