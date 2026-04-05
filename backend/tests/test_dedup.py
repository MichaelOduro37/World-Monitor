"""Tests for the duplicate detection service."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.event import Event, EventType
from app.services.dedup_service import _is_duplicate, _similarity, detect_and_mark_duplicates


def _make_event(
    *,
    event_type: EventType = EventType.earthquake,
    title: str = "Test Event",
    lat: float | None = None,
    lon: float | None = None,
    start_time: datetime | None = None,
    is_duplicate: bool = False,
) -> Event:
    e = Event(
        id=uuid.uuid4(),
        source_event_id=str(uuid.uuid4()),
        event_type=event_type,
        title=title,
        summary="",
        url="",
        start_time=start_time or datetime.now(tz=timezone.utc),
        lat=lat,
        lon=lon,
        tags=[],
        raw_payload={},
        is_duplicate=is_duplicate,
    )
    return e


# ---------------------------------------------------------------------------
# Unit tests for low-level helpers
# ---------------------------------------------------------------------------

def test_similarity_identical() -> None:
    assert _similarity("hello world", "hello world") == pytest.approx(1.0)


def test_similarity_empty() -> None:
    assert _similarity("", "something") == pytest.approx(0.0)
    assert _similarity("something", "") == pytest.approx(0.0)


def test_similarity_different() -> None:
    ratio = _similarity("earthquake in Japan", "flood in Brazil")
    assert ratio < 0.5


def test_is_duplicate_same_title_and_type() -> None:
    now = datetime.now(tz=timezone.utc)
    a = _make_event(title="Major earthquake strikes Turkey", start_time=now)
    b = _make_event(title="Major earthquake strikes Turkey", start_time=now + timedelta(minutes=30))
    assert _is_duplicate(b, a) is True


def test_is_duplicate_different_type() -> None:
    now = datetime.now(tz=timezone.utc)
    a = _make_event(event_type=EventType.earthquake, title="Disaster", start_time=now)
    b = _make_event(event_type=EventType.flood, title="Disaster", start_time=now)
    assert _is_duplicate(b, a) is False


def test_is_duplicate_outside_time_window() -> None:
    now = datetime.now(tz=timezone.utc)
    a = _make_event(title="Wildfire in California", start_time=now - timedelta(hours=24))
    b = _make_event(title="Wildfire in California", start_time=now)
    assert _is_duplicate(b, a) is False


def test_is_duplicate_geo_proximity() -> None:
    now = datetime.now(tz=timezone.utc)
    # Different titles but very close geographically (within 75 km)
    a = _make_event(title="Quake A", lat=35.0, lon=25.0, start_time=now)
    b = _make_event(title="Quake B", lat=35.1, lon=25.1, start_time=now + timedelta(minutes=5))
    assert _is_duplicate(b, a) is True


def test_is_duplicate_geo_too_far() -> None:
    now = datetime.now(tz=timezone.utc)
    # Same title but far apart (>75 km)
    a = _make_event(title="Flood event", lat=0.0, lon=0.0, start_time=now)
    b = _make_event(title="Flood report", lat=10.0, lon=10.0, start_time=now)
    # title similarity is low AND geo is too far → not a dup
    assert _is_duplicate(b, a) is False


def test_is_duplicate_no_coords_falls_back_to_title() -> None:
    now = datetime.now(tz=timezone.utc)
    a = _make_event(title="6.5 magnitude earthquake near Indonesia coast", start_time=now)
    b = _make_event(title="6.5 magnitude earthquake near Indonesia coast", start_time=now + timedelta(hours=1))
    assert _is_duplicate(b, a) is True


# ---------------------------------------------------------------------------
# Integration test: detect_and_mark_duplicates uses the session
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_detect_and_mark_no_events() -> None:
    """Should be a no-op when the list is empty."""
    session = MagicMock()
    await detect_and_mark_duplicates([], session)
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_detect_and_mark_within_batch(db_session) -> None:
    """Two identical new events in the same batch: second should be marked dup."""
    from sqlalchemy.ext.asyncio import AsyncSession

    now = datetime.now(tz=timezone.utc)
    e1 = _make_event(title="Big earthquake near coast", start_time=now)
    e2 = _make_event(title="Big earthquake near coast", start_time=now + timedelta(minutes=10))

    # Add both to the session so SQLAlchemy tracks them
    db_session.add(e1)
    db_session.add(e2)
    await db_session.flush()

    await detect_and_mark_duplicates([e1, e2], db_session)
    await db_session.flush()

    assert e1.is_duplicate is False
    assert e2.is_duplicate is True
    assert e2.duplicate_of_id == e1.id


@pytest.mark.asyncio
async def test_detect_and_mark_against_existing(db_session) -> None:
    """A new event that matches an existing one should be marked as duplicate."""
    now = datetime.now(tz=timezone.utc)
    existing = _make_event(title="Typhoon hits Philippines coast", start_time=now, event_type=EventType.storm)
    db_session.add(existing)
    await db_session.flush()

    new_event = _make_event(
        title="Typhoon hits Philippines coast",
        start_time=now + timedelta(hours=2),
        event_type=EventType.storm,
    )
    db_session.add(new_event)
    await db_session.flush()

    await detect_and_mark_duplicates([new_event], db_session)
    await db_session.flush()

    assert new_event.is_duplicate is True
    assert new_event.duplicate_of_id == existing.id
