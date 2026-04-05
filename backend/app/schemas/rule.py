from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RuleBase(BaseModel):
    name: str
    description: str = ""
    conditions: dict[str, Any] = {}
    actions: dict[str, Any] = {}
    is_active: bool = True


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    conditions: dict[str, Any] | None = None
    actions: dict[str, Any] | None = None
    is_active: bool | None = None


class RuleResponse(RuleBase):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
