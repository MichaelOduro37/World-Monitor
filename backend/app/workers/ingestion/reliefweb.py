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

RELIEFWEB_URL = "https://api.reliefweb.int/v1/disasters"

# ReliefWeb disaster type -> EventType
_TYPE_MAP: dict[str, EventType] = {
    "Earthquake": EventType.earthquake,
    "Tropical Cyclone": EventType.storm,
    "Flood": EventType.flood,
    "Flash Flood": EventType.flood,
    "Volcano": EventType.volcano,
    "Tsunami": EventType.tsunami,
    "Wild Fire": EventType.wildfire,
    "Fire": EventType.wildfire,
    "Epidemic": EventType.outbreak,
    "Drought": EventType.other,
    "Landslide": EventType.other,
    "Cold Wave": EventType.other,
    "Heat Wave": EventType.other,
    "Storm Surge": EventType.storm,
    "Extratropical Cyclone": EventType.storm,
    "Technological Disaster": EventType.other,
    "Civil Unrest": EventType.conflict,
    "Conflict": EventType.conflict,
    "Complex Emergency": EventType.conflict,
    "Insect Infestation": EventType.other,
    "Snow Avalanche": EventType.other,
    "Other": EventType.other,
}

# ReliefWeb alert level -> severity
_ALERT_SEVERITY: dict[str, float] = {
    "red": 0.9,
    "orange": 0.65,
    "green": 0.3,
    "": 0.3,
}


class ReliefWebIngestor(BaseIngestor):
    """Ingestor for the UN OCHA ReliefWeb Disasters API."""

    def __init__(
        self,
        source_id: uuid.UUID | None = None,
        url: str = RELIEFWEB_URL,
        limit: int = 100,
    ) -> None:
        self.source_id = source_id
        self.url = url
        self.limit = limit

    async def fetch(self) -> List[EventCreate]:
        payload = {
            "limit": self.limit,
            "sort": ["date:desc"],
            "fields": {
                "include": [
                    "name",
                    "date",
                    "country",
                    "type",
                    "status",
                    "glide",
                    "url",
                    "description",
                    "alert_level",
                ]
            },
            "filter": {
                "field": "status",
                "value": ["alert", "ongoing", "past"],
            },
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.url,
                    json=payload,
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.error("ReliefWeb fetch failed: %s", exc)
            return []

        events: List[EventCreate] = []
        for item in data.get("data", []):
            fields = item.get("fields", {})
            item_id = str(item.get("id", uuid.uuid4()))

            name = fields.get("name", "ReliefWeb Disaster")
            description = fields.get("description", "")

            # Date
            date_info = fields.get("date", {})
            created_str = date_info.get("created") or date_info.get("event") or ""
            start_time: datetime
            if created_str:
                try:
                    start_time = datetime.fromisoformat(
                        created_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    start_time = datetime.now(tz=timezone.utc)
            else:
                start_time = datetime.now(tz=timezone.utc)

            # Country
            countries = fields.get("country", [])
            country_names = [c.get("name", "") for c in countries if c.get("name")]
            country = country_names[0] if country_names else None

            # Disaster type
            type_list = fields.get("type", [])
            event_type = EventType.other
            type_names: list[str] = []
            for t in type_list:
                tname = t.get("name", "")
                type_names.append(tname)
                if tname in _TYPE_MAP:
                    event_type = _TYPE_MAP[tname]
                    break

            # Severity from alert level
            alert_level = (fields.get("alert_level") or "").lower()
            severity = _ALERT_SEVERITY.get(alert_level, 0.3)

            url_str = fields.get("url", "") or ""
            glide = fields.get("glide", "")
            status = fields.get("status", "")

            tags = ["reliefweb"] + [t.lower().replace(" ", "-") for t in type_names]
            if status:
                tags.append(status)
            if glide:
                tags.append(glide)

            events.append(
                EventCreate(
                    source_id=self.source_id,
                    source_event_id=f"RW-{item_id}",
                    event_type=event_type,
                    title=name,
                    summary=description[:500] if description else f"ReliefWeb disaster: {name}. Countries: {', '.join(country_names)}.",
                    url=url_str,
                    start_time=start_time,
                    country=country,
                    severity=severity,
                    tags=tags,
                    raw_payload=fields,
                )
            )

        logger.info("ReliefWeb: fetched %d disaster events", len(events))
        return events
