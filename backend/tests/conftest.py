from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.models import User, Event, Source, Subscription, Rule  # noqa: F401 – register with Base

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "test_worldmonitor.db")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

# Teach SQLite to render JSONB as plain JSON
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler  # noqa: E402

if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
    SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "JSON"  # type: ignore[attr-defined]

_test_engine = create_async_engine(TEST_DATABASE_URL)
_TestSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_tables():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _test_engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.unlink(TEST_DB_PATH)


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables():
    """Delete all rows between tests for isolation."""
    yield
    async with _test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    from app.main import app
    import app.database as db_module

    app.dependency_overrides[get_db] = override_get_db

    with patch.object(db_module, "engine", _test_engine):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data() -> dict:
    return {
        "email": "testuser@example.com",
        "password": "securepassword123",
        "full_name": "Test User",
    }


@pytest.fixture
def admin_user_data() -> dict:
    return {
        "email": "admin@example.com",
        "password": "adminpassword123",
        "full_name": "Admin User",
    }


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user_data: dict) -> dict:
    """Register a regular user and return Bearer auth headers."""
    reg = await client.post("/api/v1/auth/register", json=test_user_data)
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(
    client: AsyncClient,
    admin_user_data: dict,
    db_session: AsyncSession,
) -> dict:
    """Register a user, promote to admin via DB, and return Bearer auth headers."""
    from sqlalchemy import select
    from app.models.user import User, UserRole

    reg = await client.post("/api/v1/auth/register", json=admin_user_data)
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    result = await db_session.execute(
        select(User).where(User.email == admin_user_data["email"])
    )
    user = result.scalars().first()
    assert user is not None
    user.role = UserRole.admin
    db_session.add(user)
    await db_session.flush()

    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def make_event(db_session: AsyncSession):
    """Factory fixture to insert Event rows directly into the test DB."""
    import uuid
    from datetime import datetime, timezone
    from app.models.event import Event, EventType

    created: list[Event] = []

    async def _factory(
        *,
        event_type: EventType = EventType.earthquake,
        title: str = "Test Event",
        summary: str = "Test summary",
        lat: float | None = None,
        lon: float | None = None,
        severity: float | None = None,
        start_time: datetime | None = None,
        **kwargs,
    ) -> Event:
        event = Event(
            id=uuid.uuid4(),
            source_event_id=str(uuid.uuid4()),
            event_type=event_type,
            title=title,
            summary=summary,
            lat=lat,
            lon=lon,
            severity=severity,
            start_time=start_time or datetime.now(tz=timezone.utc),
            tags=[],
            raw_payload={},
            **kwargs,
        )
        db_session.add(event)
        await db_session.flush()
        created.append(event)
        return event

    return _factory
