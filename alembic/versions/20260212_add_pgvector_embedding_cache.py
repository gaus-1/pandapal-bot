"""add pgvector and embedding_cache

Revision ID: 20260212_pgvector
Revises: 20260212_drop_news
Create Date: 2026-02-12

Расширение pgvector и таблица embedding_cache для семантического кеша RAG.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260212_pgvector"
down_revision: Union[str, None] = "20260212_drop_news"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS embedding_cache (
            id SERIAL PRIMARY KEY,
            query_text TEXT NOT NULL,
            embedding vector(256),
            result_json JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS embedding_cache_embedding_idx
        ON embedding_cache
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )


def downgrade() -> None:
    op.drop_table("embedding_cache", if_exists=True)
    op.execute("DROP EXTENSION IF EXISTS vector")
