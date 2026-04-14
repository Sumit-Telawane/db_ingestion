"""
Ingest route — POST /ingest

Accepts a full document payload (chunks + embeddings + metadata) from the
NLP microservice and delegates persistence to the StorageOrchestrator.
"""


from fastapi import APIRouter, HTTPException, Request, status

from core.logger import setup_logger
from core.orchestrators.storage_orchestrator import StorageOrchestrator
from core.schema import IngestRequest, IngestResponse

logger = setup_logger("ingest_route")

router = APIRouter(prefix="/ingest", tags=["Ingest"])


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a chunked document",
    description=(
        "Accepts chunked document data with embeddings and metadata. "
        "Stores structured data in PostgreSQL and embedding vectors in Milvus. "
        "The same chunk UUID is used as the primary key in both databases."
    ),
)
async def ingest_document(
    payload: IngestRequest,
    request: Request,
) -> IngestResponse:
    """
    Persist a chunked document to PostgreSQL and Milvus.

    - Structured metadata → PostgreSQL (documents + chunks tables).
    - Embedding vectors   → Milvus (document_chunks collection).

    The chunk_id primary key is **identical** in both stores.
    """
    try:
        orchestrator: StorageOrchestrator = request.app.state.container.resolve(
            StorageOrchestrator
        )
        result = await orchestrator.ingest(payload)

        return IngestResponse(
            document_id=result["document_id"],
            file_name=result["file_name"],
            total_chunks=result["total_chunks"],
        )

    except Exception as e:
        logger.error(
            f"service='ingest_route' "
            f"message='Request handling failed' "
            f"file_name='{payload.file_name}' "
            f"error='{str(e)}' exception='{type(e).__name__}'"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {type(e).__name__}: {str(e)}",
        )
