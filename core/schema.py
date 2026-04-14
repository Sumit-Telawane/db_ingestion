"""
Pydantic schemas for the Storage Microservice.

Inbound  → IngestRequest   (what the ingestion service POSTs to us)
Outbound → IngestResponse  (what we return to the caller)
"""

from typing import Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Entity sub-model
# ---------------------------------------------------------------------------

class Entity(BaseModel):
    text: str
    label: str


# ---------------------------------------------------------------------------
# Single chunk payload  (matches ingestion-service output exactly)
# ---------------------------------------------------------------------------

class ChunkPayload(BaseModel):
    chunk_id: str
    raw_text: str
    embedding: list[float]

    token_count: int | None = None
    headings: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    entity: list[Entity] = Field(default_factory=list)   # field name is "entity" in source JSON
    image_uri: str | None = None
    page_no: int | None = None
    has_table: bool = False
    has_image: bool = False


# ---------------------------------------------------------------------------
# Top-level ingest request
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    file_name: str
    total_chunks: int
    chunks: list[ChunkPayload]


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class IngestResponse(BaseModel):
    document_id: str
    file_name: str
    total_chunks: int
    message: str = "Document ingested successfully"