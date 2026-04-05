from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.event import EventType


class EventBase(BaseModel):
    source_event_id: str
    event_type: EventType
    title: str = ""
    summary: str = ""
    url: str = ""
    start_time: datetime
    updated_time: datetime | None = None
    lat: float | None = None
    lon: float | None = None
    country: str | None = None
    region: str | None = None
    severity: float | None = Field(default=None, ge=0.0, le=1.0)
    tags: list[str] = []
    raw_payload: dict[str, Any] = {}
    is_duplicate: bool = False
    duplicate_of_id: uuid.UUID | None = None


class EventCreate(EventBase):
    source_id: uuid.UUID | None = None


class EventUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    severity: float | None = Field(default=None, ge=0.0, le=1.0)
    country: str | None = None
    region: str | None = None
    tags: list[str] | None = None
    is_duplicate: bool | None = None
    duplicate_of_id: uuid.UUID | None = None


class EventResponse(EventBase):
    id: uuid.UUID
    source_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[EventResponse]
