"""
Storage Orchestrator — coordinates the full ingestion flow.

Flow
----
1. Build chunk rows (PG) + vector rows (Milvus) using shared deterministic UUIDs.
2. Write to PostgreSQL via DocumentRepository (owns its session lifecycle).
3. Write to Milvus after PG commits (Milvus has no rollback — write only on PG success).

Session management
------------------
The orchestrator has no knowledge of sessions or connections.
DocumentRepository handles the full PG transaction internally via the
injected AsyncSessionFactory.  The orchestrator simply calls the repo method
and awaits the result.
"""

import uuid

from core.logger import setup_logger
from core.schema import IngestRequest
from core.services.postgres_service import build_chunk_rows
from core.services.milvus_service import build_vector_rows
from core.utils.log_utils import log_error, log_info
from infrastructure.postgres_db.repositories.document_repository import DocumentRepository
from infrastructure.milvus_db.repositories.vector_repository import VectorRepository

logger = setup_logger("storage_orchestrator")


class StorageOrchestrator:
    """
    Orchestrates document + chunk persistence across PostgreSQL and Milvus.

    Dependencies are injected via the DI container (punq).
    """

    def __init__(
        self,
        document_repository: DocumentRepository,
        vector_repository: VectorRepository,
    ) -> None:
        self._doc_repo = document_repository
        self._vec_repo = vector_repository

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def ingest(self, request: IngestRequest) -> dict:
        """
        Persist a full document (metadata + chunks + vectors).

        Args:
            request: Validated IngestRequest from the route layer.

        Returns:
            dict with document_id, file_name, total_chunks, chunk_ids.
        """
        log_info(
            logger,
            service='storage_orchestrator',
            message='Ingest process started',
            file_name=request.file_name,
            total_chunks=request.total_chunks,
        )

        try:
            document_id, chunk_uuids = await self._persist_document(request)

            log_info(
                logger,
                service='storage_orchestrator',
                message='Ingest process completed',
                document_id=document_id,
                chunks_stored=len(chunk_uuids),
            )

            return {
                "document_id":  str(document_id),
                "file_name":    request.file_name,
                "total_chunks": request.total_chunks,
                "chunk_ids":    chunk_uuids,
            }

        except Exception as e:
            log_error(
                logger,
                service='storage_orchestrator',
                message='Ingest process failed',
                error=e,
                file_name=request.file_name,
                exception=type(e).__name__,
            )
            raise

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _persist_document(
        self,
        request: IngestRequest,
    ) -> tuple[uuid.UUID, list[str]]:
        """
        Build rows, persist to PG, then persist vectors to Milvus.

        PG write completes (and commits) before Milvus write starts —
        Milvus has no ACID rollback so we only write once PG succeeds.

        Returns:
            (document_id UUID, list of chunk UUID strings)
        """
        # Step 1 — generate a document_id and build all rows up front
        document_id = uuid.uuid4()
        pg_chunk_rows, chunk_uuids = build_chunk_rows(document_id, request.chunks)

        # Step 2 — persist document + all chunks to PG in one transaction
        # (DocumentRepository owns the session — orchestrator has no session knowledge)
        try:
            await self._doc_repo.insert_document_with_chunks(
                document_id=document_id,
                file_name=request.file_name,
                total_chunks=request.total_chunks,
                chunk_rows=pg_chunk_rows,
            )
        except Exception as e:
            log_error(
                logger,
                service='storage_orchestrator',
                message='PostgreSQL insert failed',
                error=e,
                exception=type(e).__name__,
            )
            raise

        log_info(
            logger,
            service='storage_orchestrator',
            message='PostgreSQL insert completed',
            document_id=document_id,
        )

        # Step 3 — persist vectors to Milvus
        vector_rows = build_vector_rows(
            document_id=str(document_id),
            chunks=request.chunks,
            chunk_uuids=chunk_uuids,
        )

        try:
            await self._vec_repo.bulk_insert_vectors(vector_rows)

        except Exception as e:
            log_error(
                logger,
                service='storage_orchestrator',
                message='Milvus vector insert failed',
                error=e,
                document_id=document_id,
                exception=type(e).__name__,
            )
            raise

        log_info(
            logger,
            service='storage_orchestrator',
            message='Milvus vector insert completed',
            document_id=document_id,
        )

        return document_id, chunk_uuids