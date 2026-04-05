from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    event_types: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    min_severity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    keywords: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    geo_fence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notify_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_whatsapp: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notify_webpush: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[object] = relationship("User", back_populates="subscriptions")
