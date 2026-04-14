from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility
)

# =========================
# 1. Connect to Milvus
# =========================
connections.connect(
    alias="default",
    host="localhost",
    port="19530"
)

COLLECTION_NAME = "document_chunks"

# =========================
# 2. Drop if exists (optional for dev)
# =========================
if utility.has_collection(COLLECTION_NAME):
    utility.drop_collection(COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' deleted successfully ✅")
else:
    print(f"Collection '{COLLECTION_NAME}' does not exist ❌")

# =========================
# 3. Define Schema
# =========================
fields = [
    FieldSchema(
        name="chunk_id",
        dtype=DataType.VARCHAR,
        max_length=36,
        is_primary=True,
        auto_id=False
    ),
    FieldSchema(
        name="document_id",
        dtype=DataType.VARCHAR,
        max_length=36
    ),
    FieldSchema(
        name="has_table",
        dtype=DataType.BOOL
    ),
    FieldSchema(
        name="has_image",
        dtype=DataType.BOOL
    ),
    FieldSchema(
        name="embedding",
        dtype=DataType.FLOAT_VECTOR,
        dim=768   # match your embedding model
    )
]

schema = CollectionSchema(
    fields,
    description="Document chunk embeddings"
)

# =========================
# 4. Create Collection
# =========================
collection = Collection(
    name=COLLECTION_NAME,
    schema=schema
)

# =========================
# 5. Create Index (CRITICAL)
# =========================
index_params = {
    "metric_type": "COSINE",
    "index_type": "HNSW",
    "params": {
        "M": 8,
        "efConstruction": 64
    }
}

collection.create_index(
    field_name="embedding",
    index_params=index_params
)

# =========================
# 6. Load Collection
# =========================
collection.load()

print(f"Collection '{COLLECTION_NAME}' is ready 🚀")
