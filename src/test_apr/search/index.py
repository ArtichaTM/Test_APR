"""Elasticsearch index setup and search/index/delete helpers.

Per spec, the index only stores `id` (as the ES document `_id`, so we don't
duplicate it into `_source`) and `text`. Ordering by `created_date` and
pagination happen against Postgres in `test_apr.app`, since that data isn't
present in the index.
"""

from collections.abc import AsyncIterable

from elasticsearch import NotFoundError
from elasticsearch.helpers import async_bulk

from test_apr import config
from test_apr.search.client import get_client

INDEX_NAME = config.ELASTICSEARCH_INDEX

# `russian` and `english` are built-in ES analyzers (stemming + stopwords),
# no plugin required. `text` uses the Russian analyzer since the sample data
# is predominantly Russian, with an `english` sub-field searched in parallel
# so English-language documents/queries are still matched reasonably.
INDEX_BODY = {
    "mappings": {
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
}


async def init_index() -> None:
    """Create the index with its mapping if it does not already exist."""
    client = get_client()
    exists = await client.indices.exists(index=INDEX_NAME)
    if not exists:
        await client.indices.create(index=INDEX_NAME, body=INDEX_BODY)


async def index_document(doc_id: str, text: str) -> None:
    client = get_client()
    await client.index(index=INDEX_NAME, id=doc_id, body={"text": text})


async def bulk_index_documents(documents: AsyncIterable[dict] | list[dict]) -> None:
    """Bulk-index `{"id": ..., "text": ...}` dicts. Used by the CSV import command."""
    client = get_client()

    async def _actions():
        if isinstance(documents, list):
            for doc in documents:
                yield {"_index": INDEX_NAME, "_id": doc["id"], "_source": {"text": doc["text"]}}
        else:
            async for doc in documents:
                yield {"_index": INDEX_NAME, "_id": doc["id"], "_source": {"text": doc["text"]}}

    await async_bulk(client, _actions())


async def delete_document(doc_id: str) -> None:
    """Delete a document from the index.

    Missing documents are treated as an already-successful deletion (the
    end state - "not indexed" - matches what the caller wants), so
    `NotFoundError` is swallowed rather than propagated.
    """
    client = get_client()
    try:
        await client.delete(index=INDEX_NAME, id=doc_id)
    except NotFoundError:
        pass


async def search_ids(query: str, max_candidates: int) -> list[str]:
    """Return matching document ids ranked by relevance, capped at `max_candidates`."""
    client = get_client()
    response = await client.search(
        index=INDEX_NAME,
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["text", "text.english"],
                }
            },
            "size": max_candidates,
            "_source": False,
        },
    )
    return [hit["_id"] for hit in response["hits"]["hits"]]
