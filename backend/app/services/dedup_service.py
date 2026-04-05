from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event

logger = logging.getLogger(__name__)

# Tuning knobs
_TITLE_SIMILARITY_THRESHOLD = 0.82  # SequenceMatcher ratio
_TIME_WINDOW_HOURS = 12             # only compare events within this window
_GEO_PROXIMITY_KM = 75.0           # consider geo-duplicate if within this radius


def _similarity(a: str, b: str) -> float:
    """Return string similarity ratio in [0, 1]."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two points."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _is_geo_duplicate(event: Event, candidate: Event) -> bool:
    """Return True if both events have coordinates and are within the proximity radius."""
    if (
        event.lat is None
        or event.lon is None
        or candidate.lat is None
        or candidate.lon is None
    ):
        return False
    dist = _haversine_km(event.lat, event.lon, candidate.lat, candidate.lon)
    return dist <= _GEO_PROXIMITY_KM


def _is_duplicate(event: Event, candidate: Event) -> bool:
    """Determine whether *event* is a duplicate of *candidate*.

    Rules (all must hold):
    1. Same event type.
    2. Time difference ≤ _TIME_WINDOW_HOURS.
    3. Title similarity ≥ _TITLE_SIMILARITY_THRESHOLD  OR  geographic proximity.
    """
    if event.event_type != candidate.event_type:
        return False

    time_diff = abs(
        (event.start_time - candidate.start_time).total_seconds()
    )
    if time_diff > _TIME_WINDOW_HOURS * 3600:
        return False

    title_sim = _similarity(event.title, candidate.title)
    if title_sim >= _TITLE_SIMILARITY_THRESHOLD:
        return True

    if _is_geo_duplicate(event, candidate):
        return True

    return False


async def detect_and_mark_duplicates(
    new_events: list[Event],
    session: AsyncSession,
) -> None:
    """For each new event, search for existing events that are duplicates and mark them.

    The *newer* event is always marked as the duplicate; the *older* (canonical)
    event retains ``is_duplicate=False``.
    """
    if not new_events:
        return

    earliest = min(e.start_time for e in new_events)
    window_start = earliest - timedelta(hours=_TIME_WINDOW_HOURS)

    # Fetch recent existing events (not already marked as duplicates) once,
    # excluding the new events themselves so we don't consider them as "existing".
    new_event_ids = [e.id for e in new_events]

    result = await session.execute(
        select(Event).where(
            and_(
                Event.start_time >= window_start,
                Event.is_duplicate.is_(False),
                Event.id.notin_(new_event_ids),
            )
        )
    )
    existing: list[Event] = list(result.scalars().all())

    # Index existing by id for quick lookup
    existing_by_id: dict[uuid.UUID, Event] = {e.id: e for e in existing}

    # Also track ids of the new events being processed so we can compare
    # new-vs-new as well (within the same batch)
    processed: list[Event] = []

    for event in new_events:
        canonical: Event | None = None

        # Check against already-existing events
        for candidate in existing:
            if candidate.id == event.id:
                continue
            if _is_duplicate(event, candidate):
                canonical = candidate
                break

        # Check within the current batch (new vs. new)
        if canonical is None:
            for candidate in processed:
                if candidate.id == event.id:
                    continue
                if _is_duplicate(event, candidate):
                    canonical = candidate
                    break

        if canonical is not None:
            event.is_duplicate = True
            event.duplicate_of_id = canonical.id
            session.add(event)
            logger.debug(
                "Marked event %s ('%s') as duplicate of %s ('%s')",
                event.id,
                event.title[:60],
                canonical.id,
                canonical.title[:60],
            )
        else:
            processed.append(event)
            existing_by_id[event.id] = event
