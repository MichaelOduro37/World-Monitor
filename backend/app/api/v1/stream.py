from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event, EventType
from app.schemas.event import EventResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["stream"])

_POLL_INTERVAL = 10  # seconds between DB polls
_MAX_EVENTS_PER_POLL = 20
_KEEPALIVE_INTERVAL = 30  # send a comment line this often (seconds)


def _event_to_dict(event: Event) -> dict:
    return EventResponse.model_validate(event).model_dump(mode="json")


async def _event_generator(
    since: datetime,
    event_type: EventType | None,
    session: AsyncSession,
) -> AsyncGenerator[str, None]:
    """Poll the database for new events and yield SSE-formatted data lines."""
    last_seen = since
    idle_ticks = 0

    while True:
        await asyncio.sleep(_POLL_INTERVAL)
        idle_ticks += 1

        try:
            filters = [Event.created_at > last_seen]
            if event_type is not None:
                filters.append(Event.event_type == event_type)

            result = await session.execute(
                select(Event)
                .where(*filters)
                .order_by(Event.created_at.asc())
                .limit(_MAX_EVENTS_PER_POLL)
            )
            new_events = list(result.scalars().all())
        except Exception as exc:
            logger.warning("SSE poll error: %s", exc)
            yield ": error polling\n\n"
            continue

        if new_events:
            last_seen = max(e.created_at for e in new_events)
            idle_ticks = 0
            for event in new_events:
                data = json.dumps(_event_to_dict(event))
                yield f"data: {data}\n\n"
        else:
            # Send a keepalive comment to prevent proxy timeouts
            if idle_ticks * _POLL_INTERVAL >= _KEEPALIVE_INTERVAL:
                yield ": keepalive\n\n"
                idle_ticks = 0


@router.get(
    "/events",
    summary="Server-Sent Events stream of new events",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def stream_events(
    since: datetime | None = Query(
        default=None,
        description="Only return events created after this ISO8601 timestamp. "
        "Defaults to now.",
    ),
    type: EventType | None = Query(default=None, description="Filter by event type"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream new events as Server-Sent Events (SSE).

    Connect with ``EventSource`` from the browser. Each event is a JSON object
    matching the ``EventResponse`` schema.
    """
    since_dt = since if since is not None else datetime.now(tz=timezone.utc)

    return StreamingResponse(
        _event_generator(since_dt, type, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
