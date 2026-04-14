"""
Milvus repository — vector insert operations via AsyncMilvusClient.

AsyncMilvusClient (pymilvus >= 2.5.3) is natively async — no thread-pool
executor needed.  All insert calls are true coroutines that yield control
to the event loop while waiting for the Milvus gRPC response.
"""

from pymilvus import AsyncMilvusClient

from core.config import setting
from core.logger import setup_logger

logger = setup_logger("vector_repository")


class VectorRepository:
    """Handles all insert operations against the Milvus collection."""

    def __init__(self, client: AsyncMilvusClient) -> None:
        self._client = client

    async def bulk_insert_vectors(
        self,
        rows: list[dict],
    ) -> None:
        """
        Insert a batch of vector rows into Milvus.

        Each dict must contain:
            chunk_id    (str  — UUID string, primary key)
            document_id (str  — UUID string)
            has_table   (bool)
            has_image   (bool)
            embedding   (list[float] — dim 768)

        AsyncMilvusClient.insert() accepts a list-of-dicts (row format)
        directly — no manual columnar conversion required.
        """
        await self._client.insert(
            collection_name=setting.MILVUS_COLLECTION,
            data=rows,
        )