"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import declarative_base, Mapped, mapped_column


Base = declarative_base()


class Document(Base):
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
