from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

_BASE = "/api/v1/sources"

_SOURCE_PAYLOAD = {
    "name": "USGS Feed",
    "source_type": "usgs",
    "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.atom",
    "is_active": True,
    "config": {},
}


@pytest.mark.asyncio
async def test_list_sources_unauthenticated(client: AsyncClient) -> None:
    response = await client.get(_BASE)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_sources_non_admin_forbidden(
    client: AsyncClient, auth_headers: dict
) -> None:
    response = await client.get(_BASE, headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_sources_empty(client: AsyncClient, admin_headers: dict) -> None:
    response = await client.get(_BASE, headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_source_non_admin_forbidden(
    client: AsyncClient, auth_headers: dict
) -> None:
    response = await client.post(_BASE, json=_SOURCE_PAYLOAD, headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_source_success(
    client: AsyncClient, admin_headers: dict
) -> None:
    response = await client.post(_BASE, json=_SOURCE_PAYLOAD, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == _SOURCE_PAYLOAD["name"]
    assert data["source_type"] == _SOURCE_PAYLOAD["source_type"]
    assert "id" in data


@pytest.mark.asyncio
async def test_create_source_duplicate_name(
    client: AsyncClient, admin_headers: dict
) -> None:
    await client.post(_BASE, json=_SOURCE_PAYLOAD, headers=admin_headers)
    response = await client.post(_BASE, json=_SOURCE_PAYLOAD, headers=admin_headers)
    assert response.status_code == 409
    assert response.json()["detail"] == "Source name already exists"


@pytest.mark.asyncio
async def test_list_sources_returns_created(
    client: AsyncClient, admin_headers: dict
) -> None:
    await client.post(_BASE, json=_SOURCE_PAYLOAD, headers=admin_headers)
    response = await client.get(_BASE, headers=admin_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["name"] == _SOURCE_PAYLOAD["name"]


@pytest.mark.asyncio
async def test_update_source_success(
    client: AsyncClient, admin_headers: dict
) -> None:
    created = await client.post(_BASE, json=_SOURCE_PAYLOAD, headers=admin_headers)
    source_id = created.json()["id"]

    response = await client.put(
        f"{_BASE}/{source_id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_update_source_not_found(
    client: AsyncClient, admin_headers: dict
) -> None:
    random_id = str(uuid.uuid4())
    response = await client.put(
        f"{_BASE}/{random_id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_source_success(
    client: AsyncClient, admin_headers: dict
) -> None:
    created = await client.post(_BASE, json=_SOURCE_PAYLOAD, headers=admin_headers)
    source_id = created.json()["id"]

    del_response = await client.delete(f"{_BASE}/{source_id}", headers=admin_headers)
    assert del_response.status_code == 204

    list_response = await client.get(_BASE, headers=admin_headers)
    assert list_response.json() == []


@pytest.mark.asyncio
async def test_delete_source_not_found(
    client: AsyncClient, admin_headers: dict
) -> None:
    random_id = str(uuid.uuid4())
    response = await client.delete(f"{_BASE}/{random_id}", headers=admin_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_trigger_ingestion_success(
    client: AsyncClient, admin_headers: dict
) -> None:
    created = await client.post(_BASE, json=_SOURCE_PAYLOAD, headers=admin_headers)
    source_id = created.json()["id"]

    response = await client.post(
        f"{_BASE}/{source_id}/trigger", headers=admin_headers
    )
    assert response.status_code == 202
    data = response.json()
    assert data["source_id"] == source_id
    assert data["detail"] == "Ingestion triggered"


@pytest.mark.asyncio
async def test_trigger_ingestion_not_found(
    client: AsyncClient, admin_headers: dict
) -> None:
    random_id = str(uuid.uuid4())
    response = await client.post(
        f"{_BASE}/{random_id}/trigger", headers=admin_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_trigger_ingestion_non_admin_forbidden(
    client: AsyncClient, auth_headers: dict, admin_headers: dict
) -> None:
    created = await client.post(_BASE, json=_SOURCE_PAYLOAD, headers=admin_headers)
    source_id = created.json()["id"]

    response = await client.post(
        f"{_BASE}/{source_id}/trigger", headers=auth_headers
    )
    assert response.status_code == 403
