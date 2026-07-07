"""Pydantic schemas used for API responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    """All DB fields for a document, as returned by `/document/{id}` and `/search`."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    rubrics: list[str]
    created_date: datetime
