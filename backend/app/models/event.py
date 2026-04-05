from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EventType(str, enum.Enum):
    earthquake = "earthquake"
    storm = "storm"
    flood = "flood"
    conflict = "conflict"
    outbreak = "outbreak"
    wildfire = "wildfire"
    tsunami = "tsunami"
    volcano = "volcano"
    news = "news"
    other = "other"


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_start_time", "start_time"),
        Index("ix_events_source_event_id", "source_event_id"),
        Index("ix_events_event_type", "event_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="eventtype"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    url: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    region: Mapped[str | None] = mapped_column(String(256), nullable=True)
    severity: Mapped[float | None] = mapped_column(Float, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source: Mapped[object] = relationship("Source", back_populates="events")
    duplicate_of: Mapped[Event | None] = relationship(
        "Event", remote_side="Event.id", foreign_keys=[duplicate_of_id]
    )
