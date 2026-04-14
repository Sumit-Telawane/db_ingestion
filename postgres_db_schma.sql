-- UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- DOCUMENTS TABLE
CREATE TABLE documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_name TEXT NOT NULL,
    total_chunks INT,
    created_at TIMESTAMP DEFAULT NOW()
);


-- CHUNKS TABLE
CREATE TABLE chunks (
    chunk_id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,

    raw_text TEXT,
    token_count INT,

    page_no INT,
    has_table BOOLEAN DEFAULT FALSE,
    has_image BOOLEAN DEFAULT FALSE,

    headings JSONB DEFAULT '[]',
    keywords JSONB DEFAULT '[]',
    entities JSONB DEFAULT '[]',

    image_uri TEXT,

    tsv tsvector,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


--Indexes
-- Basic indexes
CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_page_no ON chunks(page_no);
CREATE INDEX idx_chunks_doc_page ON chunks(document_id, page_no);
-- JSON indexes
CREATE INDEX idx_chunks_keywords ON chunks USING GIN (keywords);
CREATE INDEX idx_chunks_entities ON chunks USING GIN (entities);
-- Full-text search index
CREATE INDEX idx_chunks_tsv ON chunks USING GIN (tsv);


-- Trigger Auto-Update Search Column
CREATE OR REPLACE FUNCTION update_tsv()
RETURNS trigger AS $$
BEGIN
  NEW.tsv := to_tsvector('english', NEW.raw_text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tsv_update
BEFORE INSERT OR UPDATE ON chunks
FOR EACH ROW EXECUTE FUNCTION update_tsv();



-- Example Keyword Search Query
SELECT 
    chunk_id,
    ts_rank(tsv, plainto_tsquery('english', 'revenue growth')) AS score
FROM chunks
WHERE tsv @@ plainto_tsquery('english', 'revenue growth')
ORDER BY score DESC
LIMIT 10;