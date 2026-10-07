import ast
import asyncio
import csv
import hashlib
from datetime import datetime
from pathlib import Path

import typer
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from test_apr.db import Document, async_session_factory, init_models
from test_apr.search import bulk_index_documents, close_client, init_index

cli_app = typer.Typer(help="Management commands for the document search service")


def _parse_rubrics(raw: str) -> list[str]:
    """Parse the `rubrics` CSV cell.

    The sample data stores it as a Python list repr (single-quoted), e.g.
    "['VK-1603736028819866', 'VK-11879320040']", not JSON.
    """
    if not raw:
        return []
    try:
        parsed = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return [raw]
    if isinstance(parsed, (list, tuple)):
        return [str(item) for item in parsed]
    return [str(parsed)]


def _read_rows(csv_path: Path) -> list[dict]:
    rows = []
    with csv_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            text = row["text"]
            rows.append(
                {
                    "text": text,
                    "text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "rubrics": _parse_rubrics(row.get("rubrics", "")),
                    "created_date": datetime.fromisoformat(row["created_date"]),
                }
            )
    return rows


@cli_app.command("import-csv")
def import_csv(
    csv_path: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to the CSV file"
    ),
) -> None:
    """Import documents from a CSV file (columns: text, created_date, rubrics).

    Rows whose `text` is identical to an already-stored document (or to
    another row earlier in the same file) are skipped rather than inserted
    again, so the command is safe to re-run. Duplicate detection is done via
    a unique hash column + `ON CONFLICT DO NOTHING`, so it stays cheap even
    on large files - no need for a per-row existence check.
    """
    asyncio.run(_import_csv_async(csv_path))


async def _import_csv_async(csv_path: Path) -> None:
    await init_models()
    await init_index()

    try:
        rows = _read_rows(csv_path)
        total = len(rows)

        if not rows:
            typer.echo(f"Read {total} lines, inserted 0, 0 duplicates ignored")
            return

        async with async_session_factory() as session:
            stmt = (
                pg_insert(Document)
                .values(rows)
                .on_conflict_do_nothing(index_elements=[
                    Document.text_hash, Document.rubrics
                ])
                .returning(Document.id, Document.text)
            )
            result = await session.execute(stmt)
            inserted = result.all()
            await session.commit()

        inserted_count = len(inserted)
        duplicates = total - inserted_count

        if inserted:
            await bulk_index_documents(
                [{"id": str(doc_id), "text": text} for doc_id, text in inserted]
            )

        typer.echo(
            f"Read {total} lines, "
            f"inserted {inserted_count}, "
            f"{duplicates} duplicates ignored"
        )
    finally:
        await close_client()


@cli_app.command("reindex")
def reindex() -> None:
    """Index every document stored in Postgres into Elasticsearch.

    Use it to rebuild an empty or out-of-sync index, e.g. after an
    Elasticsearch upgrade.
    """
    asyncio.run(_reindex_async())


async def _reindex_async() -> None:
    await init_models()
    await init_index()

    try:
        async with async_session_factory() as session:
            result = await session.stream(select(Document.id, Document.text))
            indexed = await bulk_index_documents(
                {"id": str(doc_id), "text": text} async for doc_id, text in result
            )
        typer.echo(f"Indexed {indexed} documents")
    finally:
        await close_client()


if __name__ == "__main__":
    cli_app()
