-- Enable pgvector extension pro semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabulka pro firemní dokumenty a jejich embeddings
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    source_type VARCHAR(50),
    chunk_index INTEGER,
    url VARCHAR(500),
    embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pro rychlé vector similarity search
CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Index pro vyhledávání podle filename
CREATE INDEX IF NOT EXISTS documents_filename_idx ON documents(filename);

-- Index pro full-text search v češtině (fallback)
CREATE INDEX IF NOT EXISTS documents_text_idx ON documents
USING gin(to_tsvector('english', text));

-- Trigger pro automatickou aktualizaci updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();