from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List

import httpx

from app.models.event import EventType
from app.schemas.event import EventCreate
from app.workers.ingestion.base import BaseIngestor

logger = logging.getLogger(__name__)

USGS_FEED_URL = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
)


def _magnitude_to_severity(magnitude: float | None) -> float | None:
    if magnitude is None:
        return None
    return min(max(magnitude / 10.0, 0.0), 1.0)


class USGSIngestor(BaseIngestor):
    """Ingestor for USGS All Day GeoJSON earthquake feed."""

    def __init__(self, source_id: uuid.UUID | None = None, url: str = USGS_FEED_URL) -> None:
        self.source_id = source_id
        self.url = url

    async def fetch(self) -> List[EventCreate]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.url)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.error("USGS fetch failed: %s", exc)
            return []

        events: List[EventCreate] = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            coords = geometry.get("coordinates", [None, None, None])

            lon = coords[0] if len(coords) > 0 else None
            lat = coords[1] if len(coords) > 1 else None

            magnitude = props.get("mag")
            ts_ms = props.get("time")
            start_time = (
                datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
                if ts_ms
                else datetime.now(tz=timezone.utc)
            )
            updated_ms = props.get("updated")
            updated_time = (
                datetime.fromtimestamp(updated_ms / 1000, tz=timezone.utc)
                if updated_ms
                else None
            )

            events.append(
                EventCreate(
                    source_id=self.source_id,
                    source_event_id=feature.get("id", str(uuid.uuid4())),
                    event_type=EventType.earthquake,
                    title=props.get("title", "Earthquake"),
                    summary=props.get("place", ""),
                    url=props.get("url", ""),
                    start_time=start_time,
                    updated_time=updated_time,
                    lat=lat,
                    lon=lon,
                    severity=_magnitude_to_severity(magnitude),
                    tags=["earthquake", f"mag:{magnitude}"] if magnitude else ["earthquake"],
                    raw_payload=feature,
                )
            )
        logger.info("USGS: fetched %d earthquake events", len(events))
        return events
