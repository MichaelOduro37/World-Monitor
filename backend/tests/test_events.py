from __future__ import annotations

import uuid

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
