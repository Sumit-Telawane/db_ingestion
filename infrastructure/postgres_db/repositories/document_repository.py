"""
PostgreSQL repository — Document and Chunk persistence.

The AsyncSessionFactory is injected via the DI container so this repository
owns its own session lifecycle — the orchestrator has no knowledge of sessions.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.logger import setup_logger
from infrastructure.postgres_db.db_connection import get_session
from infrastructure.postgres_db.orm_models import ChunkModel, DocumentModel

logger = setup_logger("postgres_repository")


class DocumentRepository:
    """Handles all INSERT / SELECT operations for documents and chunks."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------
    # Document + chunks — single transactional write
    # ------------------------------------------------------------------

    async def insert_document_with_chunks(
        self,
        *,
        document_id: uuid.UUID,
        file_name: str,
        total_chunks: int,
        chunk_rows: list[dict],
    ) -> DocumentModel:
        """
        Insert a document row and all its chunks in a single transaction.

        Args:
            document_id:   UUID for the document.
            file_name:     Original file name.
            total_chunks:  Total chunk count declared by the ingestion service.
            chunk_rows:    List of dicts ready for ChunkModel(**row) construction.

        Returns:
            The persisted DocumentModel with its generated document_id.
        """
        async with get_session(self._session_factory) as session:
            doc = DocumentModel(
                document_id=document_id,
                file_name=file_name,
                total_chunks=total_chunks,
            )
            session.add(doc)
            await session.flush()   # materialise document_id before chunks

            orm_chunks = [ChunkModel(**row) for row in chunk_rows]
            session.add_all(orm_chunks)
            await session.flush()

        return doc

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_document_by_id(
        self,
        document_id: uuid.UUID,
    ) -> DocumentModel | None:
        async with get_session(self._session_factory) as session:
            result = await session.execute(
                select(DocumentModel).where(
                    DocumentModel.document_id == document_id
                )
            )
            return result.scalar_one_or_none()