"""
PostgreSQL service — helper functions consumed by the storage orchestrator.

Responsibilities:
  - Convert raw ChunkPayload list into ORM-ready dicts.
  - Generate deterministic UUIDs shared with Milvus (same chunk_id in both DBs).
"""

import uuid

from core.schema import ChunkPayload
from core.logger import setup_logger
from core.utils.chunk_utils import derive_has_image

logger = setup_logger("postgres_service")


def build_chunk_rows(
    document_id: uuid.UUID,
    chunks: list[ChunkPayload],
) -> tuple[list[dict], list[str]]:
    """
    Convert a list of ChunkPayload objects into:
      1. A list of dicts ready for bulk ORM insert into PostgreSQL.
      2. A list of deterministic UUID strings (str) to be shared with Milvus.

    UUID strategy
    -------------
    chunk_id is generated as uuid5(document_id, source_chunk_id_str).
    This guarantees:
      - The same UUID is used in both PostgreSQL and Milvus.
      - Identical input always produces the same UUID (idempotent re-runs).
      - No coordination between the two DB writes is needed.

    Args:
        document_id: UUID of the parent document (already inserted in PG).
        chunks:      List of ChunkPayload from the ingestion service.

    Returns:
        Tuple of (pg_rows, chunk_uuid_strings).
    """
    pg_rows: list[dict] = []
    chunk_uuids: list[str] = []

    for chunk in chunks:
        # Deterministic UUID — same for PG and Milvus
        chunk_uuid = uuid.uuid5(document_id, chunk.chunk_id)
        chunk_uuids.append(str(chunk_uuid))

        # Derive has_image from image_uri (S3 URL check)
        has_image = derive_has_image(chunk.image_uri)

        pg_rows.append(
            {
                "chunk_id":     chunk_uuid,
                "document_id":  document_id,
                "raw_text":     chunk.raw_text,
                "token_count":  chunk.token_count,
                "page_no":      chunk.page_no,
                "has_table":    chunk.has_table,
                "has_image":    has_image,
                "headings":     chunk.headings,
                "keywords":     chunk.keywords,
                "entities":     [e.model_dump() for e in chunk.entity],
                "image_uri":    chunk.image_uri,
            }
        )

    return pg_rows, chunk_uuids
