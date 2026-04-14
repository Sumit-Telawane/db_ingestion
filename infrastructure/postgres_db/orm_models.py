"""
SQLAlchemy ORM models for the Storage Microservice.

Mirrors the PostgreSQL schema defined in postgres_db_schema.sql exactly.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Documents table
# ---------------------------------------------------------------------------

class DocumentModel(Base):
    __tablename__ = "documents"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.uuid_generate_v4(),
    )
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    total_chunks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # relationship — cascaded delete propagates to chunks
    chunks: Mapped[list[ChunkModel]] = relationship(
        "ChunkModel",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="noload",   # never auto-load; always explicit
    )


# ---------------------------------------------------------------------------
# Chunks table
# ---------------------------------------------------------------------------

class ChunkModel(Base):
    __tablename__ = "chunks"

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    page_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_table: Mapped[bool] = mapped_column(Boolean, default=False)
    has_image: Mapped[bool] = mapped_column(Boolean, default=False)

    headings: Mapped[list] = mapped_column(JSONB, default=list)
    keywords: Mapped[list] = mapped_column(JSONB, default=list)
    entities: Mapped[list] = mapped_column(JSONB, default=list)

    image_uri: Mapped[str | None] = mapped_column(Text, nullable=True)

    tsv: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # relationship
    document: Mapped[DocumentModel] = relationship(
        "DocumentModel",
        back_populates="chunks",
        lazy="noload",
    )