"""add knowledge_embeddings for vector search

Revision ID: 20260212_knowledge_vec
Revises: 20260212_pgvector
Create Date: 2026-02-12

Таблица knowledge_embeddings для семантического поиска по образовательному контенту.
Векторное хранилище: Wikipedia, скрапленный контент с эмбеддингами.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260212_knowledge_vec"
down_revision: Union[str, None] = "20260212_pgvector"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_embeddings (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            subject TEXT NOT NULL DEFAULT 'общее',
            source_url TEXT NOT NULL DEFAULT '',
            embedding vector(256),
            source_hash TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS knowledge_embeddings_embedding_idx
        ON knowledge_embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS knowledge_embeddings_subject_idx
        ON knowledge_embeddings (subject)
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS knowledge_embeddings_source_hash_idx
        ON knowledge_embeddings (source_hash)
        WHERE source_hash IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_table("knowledge_embeddings", if_exists=True)
