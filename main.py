"""
Storage Microservice entry point.

Exposes one endpoint on port 8002:
  POST /ingest — accepts chunked document data (embeddings + metadata)
                 and persists to PostgreSQL and Milvus.

A single DI container is built at startup. All heavy singletons
(DB engine pool, Milvus collection) are initialised once and shared
across all requests.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI

from core.container import build_container
from core.logger import setup_logger
from infrastructure.postgres_db.db_connection import dispose_engine
from infrastructure.milvus_db.load_collection import disconnect_milvus
from routes.ingest_route import router as ingest_router

logger = setup_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Startup: build the DI container (connects Milvus, warms PG pool).
    Shutdown: dispose PG engine pool and close Milvus connection.
    """
    logger.info(
        "service='main' "
        "message='Storage microservice starting up'"
    )

    container, milvus_client = await build_container()
    app.state.container = container

    logger.info(
        "service='main' "
        "message='Storage microservice ready'"
    )

    yield

    # ---- Graceful shutdown ----
    logger.info(
        "service='main' "
        "message='Storage microservice shutting down'"
    )
    await dispose_engine()
    await disconnect_milvus(milvus_client)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Storage Microservice",
        description=(
            "Dual-database storage service:\n\n"
            "- **POST /ingest** — persists chunked document data.\n"
            "  - Structured metadata → PostgreSQL (documents + chunks tables).\n"
            "  - Embedding vectors   → Milvus (document_chunks collection).\n\n"
            "The `chunk_id` primary key is **identical** in both databases, "
            "enabling seamless cross-store lookups."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(ingest_router)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8072, reload=False)