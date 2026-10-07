from collections.abc import AsyncIterable
from contextlib import suppress
from typing import Any

from elasticsearch import NotFoundError
from elasticsearch.helpers import async_bulk

from test_apr.search.client import get_client

INDEX_NAME = 'documents'

# russian/english are built-in ES analyzers (stemming + stopwords)
INDEX_MAPPINGS = {
    "properties": {
        "text": {
            "type": "text",
            "analyzer": "russian",
            "fields": {
                "english": {"type": "text", "analyzer": "english"},
            },
        }
    }
}


async def init_index() -> None:
    client = get_client()
    exists = await client.indices.exists(index=INDEX_NAME)
    if not exists:
        await client.indices.create(index=INDEX_NAME, mappings=INDEX_MAPPINGS)


async def index_document(doc_id: str, text: str) -> None:
    client = get_client()
    await client.index(index=INDEX_NAME, id=doc_id, document={"text": text})


async def bulk_index_documents(
    documents: AsyncIterable[dict[str, Any]] | list[dict[str, Any]]
) -> int:
    client = get_client()
    async def _actions():
        if isinstance(documents, list):
            for doc in documents:
                assert isinstance(doc, dict)
                yield {
                    "_index": INDEX_NAME,
                    "_id": doc.get("id"),
                    "_source": {"text": doc.get("text")}
                }
        else:
            async for doc in documents:
                yield {
                    "_index": INDEX_NAME,
                    "_id": doc["id"],
                    "_source": {"text": doc["text"]}
                }

    indexed, _ = await async_bulk(client, _actions())
    return indexed


async def delete_document(doc_id: str, does_not_exist_raise: bool = False) -> None:
    client = get_client()
    if does_not_exist_raise:
        await client.delete(index=INDEX_NAME, id=doc_id)
        return
    with suppress(NotFoundError):
        await client.delete(index=INDEX_NAME, id=doc_id)


async def search_ids(query: str, max_candidates: int) -> list[str]:
    client = get_client()
    response = await client.search(
        index=INDEX_NAME,
        query={
            "multi_match": {
                "query": query,
                "fields": ["text", "text.english"],
            }
        },
        size=max_candidates,
        source=False,
    )
    return [hit["_id"] for hit in response["hits"]["hits"]]
