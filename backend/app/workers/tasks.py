from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.event import Event
from app.models.source import Source, SourceType
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.event import EventCreate
from app.workers.celery_app import celery_app
from app.workers.enrichment import enrich_event_location
from app.services.notification_service import evaluate_and_notify

logger = logging.getLogger(__name__)


async def _save_events(events: list[EventCreate], source: Source) -> list[Event]:
    """Persist new events (skip duplicates by source_event_id)."""
    saved: list[Event] = []
    async with AsyncSessionLocal() as session:
        for ec in events:
            result = await session.execute(
                select(Event).where(
                    Event.source_event_id == ec.source_event_id,
                    Event.source_id == source.id,
                )
            )
            if result.scalars().first():
                continue  # already exists

            event = Event(
                id=uuid.uuid4(),
                source_id=source.id,
                source_event_id=ec.source_event_id,
                event_type=ec.event_type,
                title=ec.title,
                summary=ec.summary,
                url=ec.url,
                start_time=ec.start_time,
                updated_time=ec.updated_time,
                lat=ec.lat,
                lon=ec.lon,
                country=ec.country,
                region=ec.region,
                severity=ec.severity,
                tags=ec.tags,
                raw_payload=ec.raw_payload,
                is_duplicate=False,
            )

            # Reverse-geocode if location missing
            if event.lat and event.lon and not event.country:
                country, region = await enrich_event_location(event.lat, event.lon)
                event.country = country
                event.region = region

            session.add(event)
            saved.append(event)

        # Update source last_fetched
        result = await session.execute(select(Source).where(Source.id == source.id))
        src = result.scalars().first()
        if src:
            src.last_fetched = datetime.now(tz=timezone.utc)
            session.add(src)

        await session.commit()

    return saved


async def _notify_for_events(new_events: list[Event]) -> None:
    """Fetch subscriptions and dispatch notifications for new events."""
    if not new_events:
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Subscription).where(Subscription.is_active.is_(True))
        )
        subscriptions = list(result.scalars().all())

        users_result = await session.execute(select(User).where(User.is_active.is_(True)))
        users = {str(u.id): u.email for u in users_result.scalars().all()}

    for event in new_events:
        await evaluate_and_notify(event, subscriptions, users)


async def _run_ingest_source(source_id: str) -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Source).where(Source.id == uuid.UUID(source_id))
        )
        source = result.scalars().first()

    if source is None or not source.is_active:
        logger.warning("Source %s not found or inactive", source_id)
        return 0

    events_data: list[EventCreate] = []

    if source.source_type == SourceType.usgs:
        from app.workers.ingestion.usgs import USGSIngestor

        ingestor = USGSIngestor(source_id=source.id, url=source.url)
        events_data = await ingestor.fetch()
    elif source.source_type == SourceType.gdacs:
        from app.workers.ingestion.gdacs import GDACSIngestor

        ingestor = GDACSIngestor(source_id=source.id, url=source.url)
        events_data = await ingestor.fetch()
    elif source.source_type == SourceType.rss:
        from app.workers.ingestion.rss import RSSIngestor

        ingestor = RSSIngestor(feed_url=source.url, source_id=source.id)
        events_data = await ingestor.fetch()
    else:
        logger.warning("Unknown source type %s for source %s", source.source_type, source_id)
        return 0

    new_events = await _save_events(events_data, source)
    await _notify_for_events(new_events)
    return len(new_events)


async def _run_ingest_all() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Source).where(Source.is_active.is_(True))
        )
        sources = list(result.scalars().all())

    for source in sources:
        try:
            count = await _run_ingest_source(str(source.id))
            logger.info("Ingested %d new events from source %s", count, source.name)
        except Exception as exc:
            logger.error("Ingestion failed for source %s: %s", source.name, exc)


@celery_app.task(name="app.workers.tasks.ingest_source", bind=True, max_retries=3)
def ingest_source(self, source_id: str) -> dict:  # type: ignore[override]
    try:
        count = asyncio.run(_run_ingest_source(source_id))
        return {"source_id": source_id, "new_events": count}
    except Exception as exc:
        logger.error("ingest_source task failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.workers.tasks.ingest_all_sources")
def ingest_all_sources() -> dict:  # type: ignore[override]
    asyncio.run(_run_ingest_all())
    return {"status": "ok"}
