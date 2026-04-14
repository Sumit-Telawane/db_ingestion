Perfect — since you haven’t created the tables yet, I’ll give you a **clean, production-ready PostgreSQL setup** with:

* ✅ UUID support
* ✅ Full-text (BM25-style) search
* ✅ Proper indexes
* ✅ Auto-updating search column

Using **PostgreSQL**.

---

# ✅ 1️⃣ Extensions You Need

You only need **ONE mandatory extension**:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

---

## 🔍 For search — NO extra extension needed

Postgres already supports:

* `tsvector`
* `tsquery`
* `ts_rank`

👉 So **no pgvector / external extension needed for keyword search**

---

## 🚀 Optional (future upgrade)

If you want better ranking later:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

Used for fuzzy matching.

---

# 🔥 2️⃣ Final CREATE TABLE Script (Ready to Run)

This includes everything:

---

```sql
-- UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================
-- DOCUMENTS TABLE
-- ========================
CREATE TABLE documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_name TEXT NOT NULL,
    total_chunks INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ========================
-- CHUNKS TABLE
-- ========================
CREATE TABLE chunks (
    chunk_id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,

    raw_text TEXT NOT NULL,
    token_count INT NOT NULL,

    page_no INT,
    has_table BOOLEAN DEFAULT FALSE,
    has_image BOOLEAN DEFAULT FALSE,

    headings JSONB DEFAULT '[]',
    keywords JSONB DEFAULT '[]',
    entities JSONB DEFAULT '[]',

    image_base64 TEXT,

    -- 🔥 Full-text search column
    tsv tsvector,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

# ⚡ 3️⃣ Indexes (IMPORTANT)

```sql
-- Basic indexes
CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_page_no ON chunks(page_no);
CREATE INDEX idx_chunks_doc_page ON chunks(document_id, page_no);

-- JSON indexes
CREATE INDEX idx_chunks_keywords ON chunks USING GIN (keywords);
CREATE INDEX idx_chunks_entities ON chunks USING GIN (entities);

-- 🔥 Full-text search index
CREATE INDEX idx_chunks_tsv ON chunks USING GIN (tsv);
```

---

# 🔁 4️⃣ Auto-Update Search Column (CRITICAL)

This keeps `tsv` updated automatically.

```sql
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
```

---

# 🔍 5️⃣ Example Keyword Search Query

```sql
SELECT 
    chunk_id,
    ts_rank(tsv, plainto_tsquery('english', 'revenue growth')) AS score
FROM chunks
WHERE tsv @@ plainto_tsquery('english', 'revenue growth')
ORDER BY score DESC
LIMIT 10;
```

---

# 💡 6️⃣ Important Notes

---

## ✅ Why `tsvector`?

It enables:

```text
fast keyword search
ranking (BM25-like)
stemming ("running" → "run")
```

---

## ✅ Why GIN index?

```text
fast lookup on large text data
```

---

## ⚠️ Do NOT skip trigger

Without this:

```text
tsv column will become stale → bad search results
```

---

# 🚀 7️⃣ Optional Upgrade (Later)

If you want **even better hybrid search**, you can:

### Add weighted search

```sql
setweight(to_tsvector('english', raw_text), 'A')
```

### Include keywords:

```sql
NEW.tsv :=
    setweight(to_tsvector('english', NEW.raw_text), 'A') ||
    setweight(to_tsvector('english', array_to_string(NEW.keywords, ' ')), 'B');
```

---

# 🔑 Final Answer

### Extensions you need:

```sql
uuid-ossp  → REQUIRED
pg_trgm    → OPTIONAL
```

---

# ✅ You’re Now Ready For

✔ keyword search (Postgres)
✔ vector search (Milvus)
✔ hybrid search (combine both)

---

If you want next, I can help you:

👉 optimize hybrid scoring (this is where real gains happen)
👉 add reranker (huge accuracy boost)
👉 build async pipeline (very important for speed)

That’s where your system becomes **top-tier** 🚀
