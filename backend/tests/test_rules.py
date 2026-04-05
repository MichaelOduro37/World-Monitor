from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

_BASE = "/api/v1/rules"

_RULE_PAYLOAD = {
    "name": "High Severity Alert",
    "description": "Trigger when severity >= 0.8",
    "conditions": {"severity_min": 0.8},
    "actions": {"notify": ["email"]},
    "is_active": True,
}


@pytest.mark.asyncio
async def test_list_rules_unauthenticated(client: AsyncClient) -> None:
    response = await client.get(_BASE)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_rules_non_admin_forbidden(
    client: AsyncClient, auth_headers: dict
) -> None:
    response = await client.get(_BASE, headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_rules_empty(client: AsyncClient, admin_headers: dict) -> None:
    response = await client.get(_BASE, headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_rule_non_admin_forbidden(
    client: AsyncClient, auth_headers: dict
) -> None:
    response = await client.post(_BASE, json=_RULE_PAYLOAD, headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_rule_success(
    client: AsyncClient, admin_headers: dict
) -> None:
    response = await client.post(_BASE, json=_RULE_PAYLOAD, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == _RULE_PAYLOAD["name"]
    assert data["conditions"] == _RULE_PAYLOAD["conditions"]
    assert data["actions"] == _RULE_PAYLOAD["actions"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_by" in data


@pytest.mark.asyncio
async def test_list_rules_returns_created(
    client: AsyncClient, admin_headers: dict
) -> None:
    await client.post(_BASE, json=_RULE_PAYLOAD, headers=admin_headers)
    response = await client.get(_BASE, headers=admin_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["name"] == _RULE_PAYLOAD["name"]


@pytest.mark.asyncio
async def test_update_rule_success(
    client: AsyncClient, admin_headers: dict
) -> None:
    created = await client.post(_BASE, json=_RULE_PAYLOAD, headers=admin_headers)
    rule_id = created.json()["id"]

    response = await client.put(
        f"{_BASE}/{rule_id}",
        json={"name": "Updated Rule", "is_active": False},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Rule"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_rule_not_found(
    client: AsyncClient, admin_headers: dict
) -> None:
    random_id = str(uuid.uuid4())
    response = await client.put(
        f"{_BASE}/{random_id}",
        json={"name": "Ghost"},
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Rule not found"


@pytest.mark.asyncio
async def test_update_rule_non_admin_forbidden(
    client: AsyncClient, auth_headers: dict, admin_headers: dict
) -> None:
    created = await client.post(_BASE, json=_RULE_PAYLOAD, headers=admin_headers)
    rule_id = created.json()["id"]

    response = await client.put(
        f"{_BASE}/{rule_id}",
        json={"name": "No permission"},
        headers=auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_rule_success(
    client: AsyncClient, admin_headers: dict
) -> None:
    created = await client.post(_BASE, json=_RULE_PAYLOAD, headers=admin_headers)
    rule_id = created.json()["id"]

    del_response = await client.delete(f"{_BASE}/{rule_id}", headers=admin_headers)
    assert del_response.status_code == 204

    list_response = await client.get(_BASE, headers=admin_headers)
    assert list_response.json() == []


@pytest.mark.asyncio
async def test_delete_rule_not_found(
    client: AsyncClient, admin_headers: dict
) -> None:
    random_id = str(uuid.uuid4())
    response = await client.delete(f"{_BASE}/{random_id}", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Rule not found"


@pytest.mark.asyncio
async def test_delete_rule_non_admin_forbidden(
    client: AsyncClient, auth_headers: dict, admin_headers: dict
) -> None:
    created = await client.post(_BASE, json=_RULE_PAYLOAD, headers=admin_headers)
    rule_id = created.json()["id"]

    response = await client.delete(f"{_BASE}/{rule_id}", headers=auth_headers)
    assert response.status_code == 403
