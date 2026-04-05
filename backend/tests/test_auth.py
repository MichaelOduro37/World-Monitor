from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, test_user_data: dict) -> None:
    response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user_data: dict) -> None:
    # First registration
    await client.post("/api/v1/auth/register", json=test_user_data)
    # Second registration with same email
    response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "short", "full_name": "Weak"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user_data: dict) -> None:
    await client.post("/api/v1/auth/register", json=test_user_data)
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user_data: dict) -> None:
    await client.post("/api/v1/auth/register", json=test_user_data)
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user_data["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, test_user_data: dict) -> None:
    # Register a new user to avoid collision
    unique_data = {**test_user_data, "email": "me_test@example.com"}
    reg = await client.post("/api/v1/auth/register", json=unique_data)
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == unique_data["email"]
    assert data["full_name"] == unique_data["full_name"]


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, test_user_data: dict) -> None:
    unique_data = {**test_user_data, "email": "refresh_test@example.com"}
    reg = await client.post("/api/v1/auth/register", json=unique_data)
    assert reg.status_code == 201
    refresh_token = reg.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_update_me(client: AsyncClient, test_user_data: dict) -> None:
    unique_data = {**test_user_data, "email": "update_test@example.com"}
    reg = await client.post("/api/v1/auth/register", json=unique_data)
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    response = await client.put(
        "/api/v1/auth/me",
        json={"full_name": "Updated Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_me_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
