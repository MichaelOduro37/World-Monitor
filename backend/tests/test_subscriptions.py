from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

_BASE = "/api/v1/subscriptions"

_SUB_PAYLOAD = {
    "name": "My Alerts",
    "event_types": ["earthquake", "flood"],
    "min_severity": 0.3,
    "keywords": ["tsunami"],
    "notify_email": True,
    "notify_whatsapp": False,
    "notify_webpush": True,
    "is_active": True,
}


@pytest.mark.asyncio
async def test_list_subscriptions_unauthenticated(client: AsyncClient) -> None:
    response = await client.get(_BASE)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_subscription_unauthenticated(client: AsyncClient) -> None:
    response = await client.post(_BASE, json=_SUB_PAYLOAD)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_subscriptions_empty(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get(_BASE, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_subscription_success(
    client: AsyncClient, auth_headers: dict
) -> None:
    response = await client.post(_BASE, json=_SUB_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == _SUB_PAYLOAD["name"]
    assert data["event_types"] == _SUB_PAYLOAD["event_types"]
    assert data["min_severity"] == _SUB_PAYLOAD["min_severity"]
    assert "id" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_list_subscriptions_returns_created(
    client: AsyncClient, auth_headers: dict
) -> None:
    await client.post(_BASE, json=_SUB_PAYLOAD, headers=auth_headers)
    response = await client.get(_BASE, headers=auth_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["name"] == _SUB_PAYLOAD["name"]


@pytest.mark.asyncio
async def test_get_subscription_success(
    client: AsyncClient, auth_headers: dict
) -> None:
    created = await client.post(_BASE, json=_SUB_PAYLOAD, headers=auth_headers)
    sub_id = created.json()["id"]

    response = await client.get(f"{_BASE}/{sub_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == sub_id


@pytest.mark.asyncio
async def test_get_subscription_not_found(
    client: AsyncClient, auth_headers: dict
) -> None:
    random_id = str(uuid.uuid4())
    response = await client.get(f"{_BASE}/{random_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_subscription_invalid_uuid(
    client: AsyncClient, auth_headers: dict
) -> None:
    response = await client.get(f"{_BASE}/not-a-uuid", headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_subscription_success(
    client: AsyncClient, auth_headers: dict
) -> None:
    created = await client.post(_BASE, json=_SUB_PAYLOAD, headers=auth_headers)
    sub_id = created.json()["id"]

    response = await client.put(
        f"{_BASE}/{sub_id}",
        json={"name": "Updated Name", "is_active": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_subscription_not_found(
    client: AsyncClient, auth_headers: dict
) -> None:
    random_id = str(uuid.uuid4())
    response = await client.put(
        f"{_BASE}/{random_id}",
        json={"name": "Whatever"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_subscription_success(
    client: AsyncClient, auth_headers: dict
) -> None:
    created = await client.post(_BASE, json=_SUB_PAYLOAD, headers=auth_headers)
    sub_id = created.json()["id"]

    del_response = await client.delete(f"{_BASE}/{sub_id}", headers=auth_headers)
    assert del_response.status_code == 204

    get_response = await client.get(f"{_BASE}/{sub_id}", headers=auth_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_subscription_not_found(
    client: AsyncClient, auth_headers: dict
) -> None:
    random_id = str(uuid.uuid4())
    response = await client.delete(f"{_BASE}/{random_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_subscription_cross_user_isolation(
    client: AsyncClient,
    test_user_data: dict,
) -> None:
    """User B must not see or access User A's subscriptions."""
    user_a = await client.post("/api/v1/auth/register", json=test_user_data)
    token_a = user_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    created = await client.post(_BASE, json=_SUB_PAYLOAD, headers=headers_a)
    sub_id = created.json()["id"]

    user_b_data = {**test_user_data, "email": "user_b@example.com"}
    user_b = await client.post("/api/v1/auth/register", json=user_b_data)
    token_b = user_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B list returns empty
    list_resp = await client.get(_BASE, headers=headers_b)
    assert list_resp.json() == []

    # User B cannot get User A's subscription
    get_resp = await client.get(f"{_BASE}/{sub_id}", headers=headers_b)
    assert get_resp.status_code == 404

    # User B cannot update User A's subscription
    put_resp = await client.put(
        f"{_BASE}/{sub_id}", json={"name": "hacked"}, headers=headers_b
    )
    assert put_resp.status_code == 404

    # User B cannot delete User A's subscription
    del_resp = await client.delete(f"{_BASE}/{sub_id}", headers=headers_b)
    assert del_resp.status_code == 404
