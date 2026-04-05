from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event, EventType
from app.schemas.event import EventListResponse, EventResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListResponse)
async def list_events(
    type: Optional[EventType] = Query(default=None, description="Filter by event type"),
    bbox: Optional[str] = Query(
        default=None,
        description="Bounding box: min_lon,min_lat,max_lon,max_lat",
    ),
    start: Optional[datetime] = Query(default=None, description="Start datetime (ISO8601)"),
    end: Optional[datetime] = Query(default=None, description="End datetime (ISO8601)"),
    severity_min: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    q: Optional[str] = Query(default=None, description="Full-text search in title/summary"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> EventListResponse:
    filters = []
    if type is not None:
        filters.append(Event.event_type == type)
    if start is not None:
        filters.append(Event.start_time >= start)
    if end is not None:
        filters.append(Event.start_time <= end)
    if severity_min is not None:
        filters.append(Event.severity >= severity_min)
    if q:
        term = f"%{q}%"
        filters.append(
            or_(Event.title.ilike(term), Event.summary.ilike(term))
        )
    if bbox:
        parts = bbox.split(",")
        if len(parts) == 4:
            try:
                min_lon, min_lat, max_lon, max_lat = (float(p) for p in parts)
                filters.append(
                    and_(
                        Event.lat.is_not(None),
                        Event.lon.is_not(None),
                        Event.lat >= min_lat,
                        Event.lat <= max_lat,
                        Event.lon >= min_lon,
                        Event.lon <= max_lon,
                    )
                )
            except ValueError:
                pass

    base_query = select(Event).where(*filters).order_by(Event.start_time.desc())
    count_query = select(func.count()).select_from(Event).where(*filters)

    total_result = await db.execute(count_query)
    total: int = total_result.scalar_one()

    offset = (page - 1) * size
    result = await db.execute(base_query.offset(offset).limit(size))
    items = result.scalars().all()

    return EventListResponse(
        total=total,
        page=page,
        size=size,
        items=list(items),
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Event:
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalars().first()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event
