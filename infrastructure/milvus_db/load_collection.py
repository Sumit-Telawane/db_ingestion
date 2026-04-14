"""
Async Milvus connection management via AsyncMilvusClient (pymilvus >= 2.5.3).

IMPORTANT — event loop requirement
------------------------------------
AsyncMilvusClient internally uses grpc.aio which binds to the running event
loop at creation time.  Creating the client at module-import time (before
uvicorn starts its loop) causes:

    RuntimeError: Task got Future attached to a different loop

The correct pattern for FastAPI / uvicorn is to create the client inside the
`lifespan` async context manager — i.e. while the uvicorn event loop is
already running.  build_container() is an async function awaited from
lifespan, so the client is always created in the correct loop.

connect_milvus() creates the client and returns it directly.
The container owns the reference — no module-level state needed here.
disconnect_milvus() receives the same instance and closes it on shutdown.
"""

from pymilvus import AsyncMilvusClient

from core.config import setting
from core.logger import setup_logger

logger = setup_logger("milvus_db")


async def connect_milvus() -> AsyncMilvusClient:
    """
    Create and return an AsyncMilvusClient.

    Must be awaited from inside a running asyncio event loop (e.g. FastAPI
    lifespan) to avoid the grpc.aio event-loop binding error.

    The caller (container) owns the returned instance and is responsible for
    passing it to disconnect_milvus() on shutdown.

    Returns:
        A connected AsyncMilvusClient instance.
    """
    client = AsyncMilvusClient(
        uri=setting.MILVUS_URI,
        token=setting.MILVUS_TOKEN,
        db_name=setting.MILVUS_DB_NAME,
        secure=setting.SECURE,
    )

    logger.info(
        f"service='milvus_db' "
        f"message='AsyncMilvusClient connected' "
        f"uri='{setting.MILVUS_URI}' "
        f"db='{setting.MILVUS_DB_NAME}'"
    )

    return client


async def disconnect_milvus(client: AsyncMilvusClient) -> None:
    """
    Close the given AsyncMilvusClient connection.

    Args:
        client: The instance returned by connect_milvus().
    """
    await client.close()
    logger.info(
        "service='milvus_db' "
        "message='AsyncMilvusClient connection closed'"
    )