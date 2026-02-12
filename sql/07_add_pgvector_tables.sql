-- pgvector: embedding_cache и knowledge_embeddings
-- Требует: PostgreSQL с установленным расширением pgvector
-- Запуск: psql $DATABASE_URL -f sql/07_add_pgvector_tables.sql
-- Или: python scripts/run_sql.py sql/07_add_pgvector_tables.sql

CREATE EXTENSION IF NOT EXISTS vector;

-- embedding_cache для семантического кеша RAG
CREATE TABLE IF NOT EXISTS embedding_cache (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    embedding vector(256),
    result_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS embedding_cache_embedding_idx
ON embedding_cache USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- knowledge_embeddings для векторного поиска
CREATE TABLE IF NOT EXISTS knowledge_embeddings (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    subject TEXT NOT NULL DEFAULT 'общее',
    source_url TEXT NOT NULL DEFAULT '',
    embedding vector(256),
    source_hash TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS knowledge_embeddings_embedding_idx
ON knowledge_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS knowledge_embeddings_subject_idx ON knowledge_embeddings (subject);
CREATE UNIQUE INDEX IF NOT EXISTS knowledge_embeddings_source_hash_idx
ON knowledge_embeddings (source_hash) WHERE source_hash IS NOT NULL;
