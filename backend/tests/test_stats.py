"""Tests for the /api/v1/stats endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.models.event import EventType


@pytest.mark.asyncio
async def test_stats_summary_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/stats/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["last_24h"] == 0
    assert data["last_7d"] == 0
    assert data["last_30d"] == 0
    assert data["duplicate_count"] == 0
    assert isinstance(data["by_type"], dict)
    assert isinstance(data["by_severity"], dict)
    assert "generated_at" in data


@pytest.mark.asyncio
async def test_stats_summary_counts(client: AsyncClient, make_event) -> None:
    now = datetime.now(tz=timezone.utc)
    await make_event(event_type=EventType.earthquake, severity=0.8, start_time=now)
    await make_event(event_type=EventType.flood, severity=0.4, start_time=now - timedelta(hours=2))
    await make_event(event_type=EventType.earthquake, severity=0.2, start_time=now - timedelta(days=5))
    await make_event(event_type=EventType.storm, severity=0.9, start_time=now - timedelta(days=10))

    response = await client.get("/api/v1/stats/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 4
    assert data["last_24h"] == 2
    assert data["last_7d"] == 3
    assert data["last_30d"] == 4

    by_type = data["by_type"]
    assert by_type.get("earthquake") == 2
    assert by_type.get("flood") == 1
    assert by_type.get("storm") == 1

    by_sev = data["by_severity"]
    assert by_sev["critical"] == 2  # 0.8 and 0.9
    assert by_sev["medium"] == 1    # 0.4
    assert by_sev["low"] == 1       # 0.2


@pytest.mark.asyncio
async def test_stats_summary_24h_by_type(client: AsyncClient, make_event) -> None:
    now = datetime.now(tz=timezone.utc)
    await make_event(event_type=EventType.wildfire, start_time=now)
    await make_event(event_type=EventType.wildfire, start_time=now - timedelta(days=2))

    response = await client.get("/api/v1/stats/summary")
    data = response.json()

    by_type_24h = data["by_type_24h"]
    assert by_type_24h.get("wildfire") == 1


@pytest.mark.asyncio
async def test_stats_hotspots_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/stats/hotspots")
    assert response.status_code == 200
    data = response.json()
    assert data["top_countries"] == []
    assert data["top_regions"] == []
    assert data["days"] == 7


@pytest.mark.asyncio
async def test_stats_hotspots_countries(client: AsyncClient, make_event) -> None:
    now = datetime.now(tz=timezone.utc)
    await make_event(country="Turkey", start_time=now)
    await make_event(country="Turkey", start_time=now)
    await make_event(country="Japan", start_time=now)

    response = await client.get("/api/v1/stats/hotspots?days=7")
    assert response.status_code == 200
    data = response.json()

    countries = {r["country"]: r["count"] for r in data["top_countries"]}
    assert countries["Turkey"] == 2
    assert countries["Japan"] == 1


@pytest.mark.asyncio
async def test_stats_hotspots_days_filter(client: AsyncClient, make_event) -> None:
    now = datetime.now(tz=timezone.utc)
    await make_event(country="France", start_time=now)
    await make_event(country="France", start_time=now - timedelta(days=20))

    # days=1 should only see the recent event
    response = await client.get("/api/v1/stats/hotspots?days=1")
    data = response.json()
    countries = {r["country"]: r["count"] for r in data["top_countries"]}
    assert countries.get("France") == 1


@pytest.mark.asyncio
async def test_stats_hotspots_invalid_days(client: AsyncClient) -> None:
    response = await client.get("/api/v1/stats/hotspots?days=0")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_stats_hotspots_limit(client: AsyncClient, make_event) -> None:
    now = datetime.now(tz=timezone.utc)
    countries = ["Germany", "Brazil", "India", "USA", "France"]
    for c in countries:
        await make_event(country=c, start_time=now)

    response = await client.get("/api/v1/stats/hotspots?limit=3")
    data = response.json()
    assert len(data["top_countries"]) == 3
