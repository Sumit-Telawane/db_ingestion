"""
Async PostgreSQL connection pool via SQLAlchemy.

A single AsyncEngine and AsyncSessionFactory are created once at module
import time and reused for the lifetime of the process.

The AsyncSessionFactory is registered in the DI container so repositories
receive it via injection — no direct imports of get_session inside
business logic.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from core.config import setting
from core.logger import setup_logger

logger = setup_logger("postgres_db")


# ---------------------------------------------------------------------------
# Engine — created once at module import time
# ---------------------------------------------------------------------------

engine: AsyncEngine = create_async_engine(
    setting.postgres_dsn,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=setting.POSTGRES_POOL_SIZE,
    max_overflow=setting.POSTGRES_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=False,
)

# ---------------------------------------------------------------------------
# Session factory — registered in the DI container as a singleton
# ---------------------------------------------------------------------------

AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Context-manager helper used by DocumentRepository
# ---------------------------------------------------------------------------

@asynccontextmanager
async def get_session(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a transactional AsyncSession from the given factory.
    Commits on success, rolls back on any exception.

    Args:
        factory: The AsyncSessionFactory injected from the container.
    """
    async with factory() as session:
        async with session.begin():
            yield session


async def dispose_engine() -> None:
    """Gracefully close all pooled connections — call on app shutdown."""
    await engine.dispose()
    logger.info(
        "service='postgres_db' "
        "message='Connection pool disposed'"
    )