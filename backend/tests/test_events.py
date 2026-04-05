from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_events_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_events_pagination_defaults(client: AsyncClient) -> None:
    response = await client.get("/api/v1/events?page=1&size=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_events_invalid_size(client: AsyncClient) -> None:
    response = await client.get("/api/v1/events?size=0")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_events_filter_type(client: AsyncClient) -> None:
    response = await client.get("/api/v1/events?type=earthquake")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["event_type"] == "earthquake"


@pytest.mark.asyncio
async def test_get_event_not_found(client: AsyncClient) -> None:
    random_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/events/{random_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


@pytest.mark.asyncio
async def test_get_event_invalid_uuid(client: AsyncClient) -> None:
    response = await client.get("/api/v1/events/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_get_event_success(client: AsyncClient, make_event) -> None:
    event = await make_event(title="Quake in Region X")
    response = await client.get(f"/api/v1/events/{event.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(event.id)
    assert data["title"] == "Quake in Region X"


@pytest.mark.asyncio
async def test_list_events_returns_seeded_event(client: AsyncClient, make_event) -> None:
    await make_event(title="Flood in Valley")
    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Flood in Valley"


@pytest.mark.asyncio
async def test_list_events_filter_by_type_match(client: AsyncClient, make_event) -> None:
    from app.models.event import EventType

    await make_event(event_type=EventType.earthquake)
    await make_event(event_type=EventType.flood)
    response = await client.get("/api/v1/events?type=earthquake")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["event_type"] == "earthquake"


@pytest.mark.asyncio
async def test_list_events_filter_by_severity(client: AsyncClient, make_event) -> None:
    await make_event(severity=0.3)
    await make_event(severity=0.8)
    response = await client.get("/api/v1/events?severity_min=0.5")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["severity"] == 0.8


@pytest.mark.asyncio
async def test_list_events_filter_by_start(client: AsyncClient, make_event) -> None:
    now = datetime.now(tz=timezone.utc)
    await make_event(start_time=now - timedelta(days=2))
    await make_event(start_time=now)
    cutoff = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    response = await client.get(f"/api/v1/events?start={cutoff}")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_list_events_filter_by_end(client: AsyncClient, make_event) -> None:
    now = datetime.now(tz=timezone.utc)
    await make_event(start_time=now - timedelta(days=2))
    await make_event(start_time=now)
    cutoff = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    response = await client.get(f"/api/v1/events?end={cutoff}")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_list_events_search_q(client: AsyncClient, make_event) -> None:
    await make_event(title="Major Earthquake near Coast")
    await make_event(title="Tropical Storm Warning")
    response = await client.get("/api/v1/events?q=earthquake")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "Earthquake" in data["items"][0]["title"]


@pytest.mark.asyncio
async def test_list_events_search_q_in_summary(client: AsyncClient, make_event) -> None:
    await make_event(title="Event A", summary="Wildfire spreading rapidly")
    await make_event(title="Event B", summary="Normal conditions")
    response = await client.get("/api/v1/events?q=wildfire")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_list_events_filter_by_bbox(client: AsyncClient, make_event) -> None:
    await make_event(lat=10.0, lon=20.0)   # inside
    await make_event(lat=50.0, lon=60.0)   # outside
    response = await client.get("/api/v1/events?bbox=15,5,25,15")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_list_events_bbox_invalid_ignored(client: AsyncClient, make_event) -> None:
    """An invalid bbox string should be silently ignored and return all events."""
    await make_event()
    response = await client.get("/api/v1/events?bbox=not,valid,bbox")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_list_events_pagination(client: AsyncClient, make_event) -> None:
    for i in range(5):
        await make_event(title=f"Event {i}")
    page1 = await client.get("/api/v1/events?page=1&size=3")
    assert page1.status_code == 200
    p1 = page1.json()
    assert p1["total"] == 5
    assert len(p1["items"]) == 3

    page2 = await client.get("/api/v1/events?page=2&size=3")
    assert page2.status_code == 200
    p2 = page2.json()
    assert len(p2["items"]) == 2


@pytest.mark.asyncio
async def test_list_events_size_too_large(client: AsyncClient) -> None:
    response = await client.get("/api/v1/events?size=101")
    assert response.status_code == 422
