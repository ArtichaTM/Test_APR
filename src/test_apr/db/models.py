import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint('text_hash', 'rubrics', name='uq_doc_text_rubrics'),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True  # Not unique. `text_hash+rubrics` are.
    )
    rubrics: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    # Stored and returned timezone-naive, matching the source CSV.
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
