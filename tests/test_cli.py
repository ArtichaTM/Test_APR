import uuid
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import select

from test_apr.cli import _import_csv_async, _reindex_async
from test_apr.db import Document, async_session_factory
from test_apr.search import close_client, delete_document, get_client
from test_apr.search.index import INDEX_NAME

pytestmark = pytest.mark.asyncio


def _write_csv(tmp_path: Path, rows: list[tuple[str, str, str]]) -> Path:
    csv_path = tmp_path / "sample.csv"
    lines = ["text,created_date,rubrics"]
    for text, created_date, rubrics in rows:
        lines.append(f'"{text}",{created_date},"{rubrics}"')
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path


async def _cleanup(text: str) -> None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(Document).where(Document.text == text)
        )
        for row in result.scalars().all():
            await session.delete(row)
        await session.commit()


async def test_import_skips_duplicate_rows_within_same_file(tmp_path, capsys):
    text = "Строка для проверки дедупликации при импорте одного файла"
    csv_path = _write_csv(
        tmp_path,
        [
            (text, "2024-01-01 00:00:00", "['TEST-DUP']"),
            (text, "2024-01-02 00:00:00", "['TEST-DUP']"),
        ],
    )

    try:
        await _import_csv_async(csv_path)
        out = capsys.readouterr().out
        assert "Read 2 lines, inserted 1, 1 duplicates ignored" in out

        async with async_session_factory() as session:
            result = await session.execute(
                select(Document).where(Document.text == text)
            )
            assert len(result.scalars().all()) == 1
    finally:
        await _cleanup(text)


async def test_import_skips_duplicates_across_separate_runs(tmp_path, capsys):
    text = "Строка для проверки дедупликации между двумя запусками"
    csv_path = _write_csv(tmp_path, [(text, "2024-01-01 00:00:00", "['TEST-DUP']")])

    try:
        await _import_csv_async(csv_path)
        capsys.readouterr()  # discard first run's output

        await _import_csv_async(csv_path)
        out = capsys.readouterr().out
        assert "Read 1 lines, inserted 0, 1 duplicates ignored" in out

        async with async_session_factory() as session:
            result = await session.execute(
                select(Document).where(Document.text == text)
            )
            assert len(result.scalars().all()) == 1
    finally:
        await _cleanup(text)


async def test_import_parses_rubrics_list(tmp_path, capsys):
    text = "Строка для проверки парсинга рубрик"
    csv_path = _write_csv(
        tmp_path, [(text, "2024-01-01 00:00:00", "['VK-1', 'VK-2', 'VK-3']")]
    )

    try:
        await _import_csv_async(csv_path)
        capsys.readouterr()

        async with async_session_factory() as session:
            result = await session.execute(
                select(Document).where(Document.text == text)
            )
            document = result.scalar_one()
            assert document.rubrics == ["VK-1", "VK-2", "VK-3"]
    finally:
        await _cleanup(text)


async def test_reindex_indexes_documents_missing_from_es(capsys):
    text = "Строка для проверки переиндексации из базы"
    document = Document(
        text=text,
        text_hash=uuid.uuid4().hex,
        rubrics=["TEST-REINDEX"],
        created_date=datetime(2024, 1, 1),
    )
    async with async_session_factory() as session:
        session.add(document)
        await session.commit()

    try:
        await _reindex_async()
        assert "Indexed" in capsys.readouterr().out

        es_client = get_client()
        assert await es_client.exists(index=INDEX_NAME, id=str(document.id))
    finally:
        await _cleanup(text)
        await delete_document(str(document.id))
        await close_client()
