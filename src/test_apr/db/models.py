"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Document(Base):
    """A single document, mirroring the `posts.csv` structure.

    `text_hash` is a SHA-256 hex digest of `text`. It is not part of the
    public API, it only backs a unique index used by the CSV import command
    to skip duplicate rows cheaply (via `ON CONFLICT DO NOTHING`) instead of
    doing a full-text comparison per row.
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    rubrics: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    # Stored and returned timezone-naive, matching the source CSV.
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
