"""End-to-end checks against a running app, enabled by setting APP_URL."""
import asyncio
import os
import sys
import uuid
from pathlib import Path

import httpx
import pytest

APP_URL = os.getenv("APP_URL", "")

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(not APP_URL, reason="APP_URL is not set"),
]


async def _cli(*args: str) -> str:
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "test_apr.cli", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    output, _ = await process.communicate()
    assert process.returncode == 0, output.decode()
    return output.decode()


async def _search(client: httpx.AsyncClient, query: str, expected: int) -> list[dict]:
    """Search until `expected` documents are found or retries run out.

    Elasticsearch makes new documents searchable only after an index refresh.
    """
    found = []
    for _ in range(20):
        response = await client.get("/search", params={"q": query})
        assert response.status_code == 200
        found = response.json()
        if len(found) == expected:
            break
        await asyncio.sleep(0.5)
    return found


async def test_import_search_get_delete_reindex(tmp_path: Path):
    marker = f"e2e{uuid.uuid4().hex}"
    first, second = f"Первый документ {marker}", f"Второй документ {marker}"
    csv_path = tmp_path / "posts.csv"
    csv_path.write_text(
        "text,created_date,rubrics\n"
        f"\"{first}\",2024-01-01 00:00:00,\"['E2E-1']\"\n"
        f"\"{second}\",2024-01-02 00:00:00,\"['E2E-1', 'E2E-2']\"\n",
        encoding="utf-8",
    )

    async with httpx.AsyncClient(base_url=APP_URL) as client:
        try:
            output = await _cli("import-csv", str(csv_path))
            assert "Read 2 lines, inserted 2, 0 duplicates ignored" in output
            output = await _cli("import-csv", str(csv_path))
            assert "Read 2 lines, inserted 0, 2 duplicates ignored" in output

            found = await _search(client, marker, expected=2)
            assert [doc["text"] for doc in found] == [second, first]
            assert found[0]["rubrics"] == ["E2E-1", "E2E-2"]
            newest, oldest = found

            response = await client.get(f"/document/{newest['id']}")
            assert response.status_code == 200
            assert response.json() == newest

            response = await client.delete(f"/document/{newest['id']}")
            assert response.status_code == 200
            response = await client.get(f"/document/{newest['id']}")
            assert response.status_code == 404
            found = await _search(client, marker, expected=1)
            assert [doc["id"] for doc in found] == [oldest["id"]]

            assert "Indexed" in await _cli("reindex")
            found = await _search(client, marker, expected=1)
            assert [doc["id"] for doc in found] == [oldest["id"]]
        finally:
            response = await client.get("/search", params={"q": marker})
            for doc in response.json():
                await client.delete(f"/document/{doc['id']}")
