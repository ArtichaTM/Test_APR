"""Shared fixtures for functional tests.

These tests exercise the app against real Postgres/Elasticsearch instances
(the same ones from docker-compose) - there are no mocks/fakes involved.
Make sure both are reachable using the env vars in your `.env` before
running `pytest`.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import datetime

import httpx
import pytest_asyncio

from test_apr.app import app
from test_apr.db import Document, async_session_factory
from test_apr.search import INDEX_NAME, get_client


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
        text_hash=uuid.uuid4().hex,  # unique dummy hash, real hashing is CLI-import specific
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
        body={"text": document.text},
        refresh=True,  # make it immediately searchable for the test
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
