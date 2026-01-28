"""
Источники новостей для детского новостного бота.

Каждый источник реализует INewsSource интерфейс.
"""

from bot.services.news.sources.rbc_rss_source import RbcRssSource

__all__ = ["RbcRssSource"]
