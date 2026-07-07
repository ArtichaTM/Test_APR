"""Async engine/session management.

No migration tool (e.g. Alembic) is used in this project by design -
`init_models()` just creates any missing tables on startup.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from test_apr import config
from test_apr.db.models import Base

engine = create_async_engine(config.DATABASE_URL, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def init_models() -> None:
    """Create tables if they do not already exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a request-scoped session."""
    async with async_session_factory() as session:
        yield session
