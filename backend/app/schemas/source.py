from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.source import SourceType


class SourceBase(BaseModel):
    name: str
    source_type: SourceType
    url: str
    is_active: bool = True
    config: dict[str, Any] = {}


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    is_active: bool | None = None
    config: dict[str, Any] | None = None


class SourceResponse(SourceBase):
    id: uuid.UUID
    last_fetched: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
