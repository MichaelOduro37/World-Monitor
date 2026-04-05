from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "world_monitor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "ingest-all-sources": {
            "task": "app.workers.tasks.ingest_all_sources",
            "schedule": settings.INGESTION_INTERVAL_SECONDS,
        },
    },
)
