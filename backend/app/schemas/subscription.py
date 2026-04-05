from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.event import EventType


class SubscriptionBase(BaseModel):
    name: str
    event_types: list[EventType] = []
    min_severity: float = Field(default=0.0, ge=0.0, le=1.0)
    keywords: list[str] = []
    geo_fence: dict[str, Any] | None = None
    notify_email: bool = True
    notify_whatsapp: bool = False
    notify_webpush: bool = True
    is_active: bool = True


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    name: str | None = None
    event_types: list[EventType] | None = None
    min_severity: float | None = Field(default=None, ge=0.0, le=1.0)
    keywords: list[str] | None = None
    geo_fence: dict[str, Any] | None = None
    notify_email: bool | None = None
    notify_whatsapp: bool | None = None
    notify_webpush: bool | None = None
    is_active: bool | None = None


class SubscriptionResponse(SubscriptionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
