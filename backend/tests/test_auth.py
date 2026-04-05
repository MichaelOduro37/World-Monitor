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


@pytest.mark.asyncio
async def test_login_inactive_user(
    client: AsyncClient, test_user_data: dict, db_session
) -> None:
    from sqlalchemy import select
    from app.models.user import User

    await client.post("/api/v1/auth/register", json=test_user_data)
    result = await db_session.execute(
        select(User).where(User.email == test_user_data["email"])
    )
    user = result.scalars().first()
    assert user is not None
    user.is_active = False
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Inactive user"


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "not.a.valid.token"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_wrong_type(client: AsyncClient, test_user_data: dict) -> None:
    """Passing an access token where a refresh token is expected should fail."""
    unique_data = {**test_user_data, "email": "wrong_type@example.com"}
    reg = await client.post("/api/v1/auth/register", json=unique_data)
    assert reg.status_code == 201
    access_token = reg.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": access_token}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_me_password(client: AsyncClient, test_user_data: dict) -> None:
    """Changing the password should allow login with the new password."""
    unique_data = {**test_user_data, "email": "pwchange@example.com"}
    reg = await client.post("/api/v1/auth/register", json=unique_data)
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    await client.put(
        "/api/v1/auth/me",
        json={"password": "newpassword456"},
        headers={"Authorization": f"Bearer {token}"},
    )

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": unique_data["email"], "password": "newpassword456"},
    )
    assert login.status_code == 200


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@example.com", "password": "anything"},
    )
    assert response.status_code == 401
