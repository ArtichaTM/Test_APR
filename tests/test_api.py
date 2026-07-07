import uuid

import pytest

pytestmark = pytest.mark.asyncio


async def test_get_document_found(client, sample_document):
    response = await client.get(f"/document/{sample_document.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(sample_document.id)
    assert body["text"] == sample_document.text
    assert body["rubrics"] == sample_document.rubrics


async def test_get_document_not_found(client):
    response = await client.get(f"/document/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_delete_document_removes_it(client, sample_document):
    response = await client.delete(f"/document/{sample_document.id}")
    assert response.status_code == 200

    follow_up = await client.get(f"/document/{sample_document.id}")
    assert follow_up.status_code == 404


async def test_delete_missing_document_returns_404(client):
    response = await client.delete(f"/document/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_search_finds_indexed_document(client, sample_document):
    response = await client.get("/search", params={"q": "единорогов"})
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert str(sample_document.id) in ids


async def test_search_no_match_returns_empty_list(client):
    response = await client.get("/search", params={"q": "жжжнесуществующийзапрос"})
    assert response.status_code == 200
    assert response.json() == []


async def test_search_respects_limit(client, sample_document):
    response = await client.get("/search", params={"q": "единорогов", "limit": 1, "offset": 0})
    assert response.status_code == 200
    assert len(response.json()) <= 1


async def test_search_requires_query_param(client):
    response = await client.get("/search")
    assert response.status_code == 422
