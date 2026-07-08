import uuid
from collections.abc import AsyncIterator
from datetime import datetime

import httpx
import pytest_asyncio

from test_apr.app import app
from test_apr.db import Document, async_session_factory, engine
from test_apr.search import get_client
from test_apr.search.index import INDEX_NAME


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test() -> AsyncIterator[None]:
    """Drop pooled asyncpg connections after each test.

    pytest-asyncio opens a new event loop per test (function scope), but
    `engine` is a module-level singleton whose pool caches connections tied
    to whatever loop created them. Without disposing, the next test's loop
    tries to reuse a connection from a closed loop and asyncpg blows up with
    "attached to a different loop". Autouse + no dependencies means this
    fixture is set up first and torn down last, i.e. after fixtures like
    `sample_document` have already used the engine for their own cleanup.
    """
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """An HTTP client wired directly to the ASGI app, with lifespan handled."""
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest_asyncio.fixture
async def sample_document() -> AsyncIterator[Document]:
    """Insert one document into Postgres and index it in ES; clean up afterwards."""
    document = Document(
        id=uuid.uuid4(),
        text="Уникальный тестовый текст про единорогов и радугу",
        # unique dummy hash, real hashing is CLI-import specific
        text_hash=uuid.uuid4().hex,
        rubrics=["TEST-1", "TEST-2"],
        created_date=datetime(2024, 1, 1, 12, 0, 0),
    )

    async with async_session_factory() as session:
        session.add(document)
        await session.commit()

    es_client = get_client()
    await es_client.index(
        index=INDEX_NAME,
        id=str(document.id),
        document={"text": document.text},
        refresh=True,
    )

    yield document

    async with async_session_factory() as session:
        db_doc = await session.get(Document, document.id)
        if db_doc is not None:
            await session.delete(db_doc)
            await session.commit()

    try:
        await es_client.delete(index=INDEX_NAME, id=str(document.id))
    except Exception:
        pass
