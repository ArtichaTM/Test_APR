"""FastAPI application: document search service.

Endpoints:
- GET    /document/{id}  -> fetch one document from Postgres
- DELETE /document/{id}  -> delete a document from Postgres and the search index
- GET    /search         -> full-text search over the index, results ordered
                            by created_date (newest first), paginated
"""

import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from test_apr import config
from test_apr.db import Document, get_session, init_models
from test_apr.schemas import DocumentOut
from test_apr.search import close_client, delete_document as es_delete_document, init_index, search_ids


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    await init_index()
    yield
    await close_client()


app = FastAPI(
    title="Test-APR document search service",
    description="Simple full-text search service backed by PostgreS+ElasticSearch",
    lifespan=lifespan,
)


@app.get("/document/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> Document:
    document = await session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.delete("/document/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    document = await session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    await session.delete(document)
    await session.commit()

    await es_delete_document(str(document_id))

    return {"status": "ok"}


@app.get("/search", response_model=list[DocumentOut])
async def search_documents(
    q: str = Query(..., min_length=1, description="Free text search query"),
    limit: int = Query(config.SEARCH_DEFAULT_LIMIT, ge=1, le=config.SEARCH_MAX_LIMIT),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[Document]:
    matched_ids = await search_ids(q, max_candidates=config.SEARCH_MAX_CANDIDATES)
    if not matched_ids:
        return []

    ids_as_uuid = [uuid.UUID(matched_id) for matched_id in matched_ids]
    stmt = (
        select(Document)
        .where(Document.id.in_(ids_as_uuid))
        .order_by(Document.created_date.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
