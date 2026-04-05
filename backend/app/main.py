from __future__ import annotations

import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.database import engine
from app.models import User, Event, Subscription, Source, Rule  # noqa: F401 – register mappers

logger = logging.getLogger(__name__)

_metrics: dict[str, int] = defaultdict(int)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Create all tables on startup (for dev; in prod use Alembic)
    if settings.APP_ENV == "development":
        try:
            from app.database import Base

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all, checkfirst=True)
            logger.info("Database tables ensured.")
        except Exception as exc:
            logger.warning("Could not create DB tables on startup: %s", exc)
    yield
    await engine.dispose()


app = FastAPI(
    title="World Monitor API",
    description="Real-time global event monitoring platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS – allow everything in dev; require explicit origins in production
origins: list[str] = ["*"] if settings.APP_ENV == "development" else settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router)


@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/metrics", tags=["ops"])
async def metrics() -> dict:
    return dict(_metrics)


@app.middleware("http")
async def count_requests(request, call_next):  # type: ignore[no-untyped-def]
    _metrics["http_requests_total"] += 1
    response = await call_next(request)
    status_key = f"http_{response.status_code}"
    _metrics[status_key] = _metrics.get(status_key, 0) + 1
    return response
