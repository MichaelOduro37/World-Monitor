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

NASA_EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"

# EONET category id -> EventType mapping
_CATEGORY_MAP: dict[str, EventType] = {
    "wildfires": EventType.wildfire,
    "severeStorms": EventType.storm,
    "volcanoes": EventType.volcano,
    "floods": EventType.flood,
    "earthquakes": EventType.earthquake,
    "seaAndLakeIce": EventType.other,
    "landslides": EventType.other,
    "snow": EventType.other,
    "drought": EventType.other,
    "dustHaze": EventType.other,
    "manmade": EventType.other,
    "waterColor": EventType.other,
    "tempExtremes": EventType.other,
}


def _geometry_to_latlon(
    geometry: list[dict],
) -> tuple[float | None, float | None, datetime]:
    """Extract the most recent lat/lon and date from EONET geometry list."""
    lat: float | None = None
    lon: float | None = None
    ts = datetime.now(tz=timezone.utc)

    if not geometry:
        return lat, lon, ts

    # Use the last (most recent) geometry entry
    geom = geometry[-1]
    coords = geom.get("coordinates")
    date_str = geom.get("date")

    if date_str:
        try:
            ts = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            pass

    geom_type = geom.get("type", "")
    if geom_type == "Point" and coords and len(coords) >= 2:
        lon, lat = float(coords[0]), float(coords[1])
    elif geom_type == "Polygon" and coords:
        ring = coords[0]
        if ring:
            lons = [c[0] for c in ring]
            lats = [c[1] for c in ring]
            lon = sum(lons) / len(lons)
            lat = sum(lats) / len(lats)

    return lat, lon, ts


class NASAEONETIngestor(BaseIngestor):
    """Ingestor for NASA Earth Observatory Natural Event Tracker (EONET) API v3."""

    def __init__(
        self,
        source_id: uuid.UUID | None = None,
        url: str = NASA_EONET_URL,
        limit: int = 200,
        days: int = 20,
    ) -> None:
        self.source_id = source_id
        self.url = url
        self.limit = limit
        self.days = days

    async def fetch(self) -> List[EventCreate]:
        params = {
            "status": "all",
            "limit": self.limit,
            "days": self.days,
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.url, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.error("NASA EONET fetch failed: %s", exc)
            return []

        events: List[EventCreate] = []
        for item in data.get("events", []):
            eonet_id = item.get("id", str(uuid.uuid4()))
            title = item.get("title", "Natural Event")

            # Determine event type from categories
            categories = item.get("categories", [])
            event_type = EventType.other
            category_ids: list[str] = []
            for cat in categories:
                cid = cat.get("id", "")
                category_ids.append(cid)
                if cid in _CATEGORY_MAP:
                    event_type = _CATEGORY_MAP[cid]
                    break

            geometry = item.get("geometry", [])
            lat, lon, start_time = _geometry_to_latlon(geometry)

            # Collect source URLs
            sources_list = item.get("sources", [])
            url_str = sources_list[0].get("url", "") if sources_list else ""

            tags = ["nasa-eonet"] + category_ids + (["closed"] if item.get("closed") else ["open"])

            events.append(
                EventCreate(
                    source_id=self.source_id,
                    source_event_id=eonet_id,
                    event_type=event_type,
                    title=title,
                    summary=f"EONET natural event: {title}. Categories: {', '.join(category_ids)}.",
                    url=url_str,
                    start_time=start_time,
                    lat=lat,
                    lon=lon,
                    tags=tags,
                    raw_payload=item,
                )
            )

        logger.info("NASA EONET: fetched %d natural events", len(events))
        return events
