from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List
from xml.etree import ElementTree

import httpx

from app.models.event import EventType
from app.schemas.event import EventCreate
from app.workers.ingestion.base import BaseIngestor

logger = logging.getLogger(__name__)

GDACS_FEED_URL = "https://www.gdacs.org/xml/rss.xml"

# GDACS alert level -> severity mapping
_ALERT_SEVERITY: dict[str, float] = {
    "green": 0.2,
    "orange": 0.6,
    "red": 0.9,
}

_EVENT_TYPE_MAP: dict[str, EventType] = {
    "EQ": EventType.earthquake,
    "TC": EventType.storm,
    "FL": EventType.flood,
    "VO": EventType.volcano,
    "TS": EventType.tsunami,
    "WF": EventType.wildfire,
    "DR": EventType.other,
}


class GDACSIngestor(BaseIngestor):
    """Ingestor for the GDACS RSS/XML disaster feed."""

    def __init__(self, source_id: uuid.UUID | None = None, url: str = GDACS_FEED_URL) -> None:
        self.source_id = source_id
        self.url = url

    async def fetch(self) -> List[EventCreate]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.url)
                response.raise_for_status()
                xml_text = response.text
        except httpx.HTTPError as exc:
            logger.error("GDACS fetch failed: %s", exc)
            return []

        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError as exc:
            logger.error("GDACS XML parse error: %s", exc)
            return []

        ns = {
            "gdacs": "http://www.gdacs.org",
            "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
        }

        events: List[EventCreate] = []
        channel = root.find("channel")
        if channel is None:
            return []

        for item in channel.findall("item"):
            title_el = item.find("title")
            title = title_el.text if title_el is not None else "GDACS Alert"

            link_el = item.find("link")
            url_str = link_el.text if link_el is not None else ""

            desc_el = item.find("description")
            summary = desc_el.text if desc_el is not None else ""

            pub_date_el = item.find("pubDate")
            start_time: datetime
            if pub_date_el is not None and pub_date_el.text:
                try:
                    from email.utils import parsedate_to_datetime
                    start_time = parsedate_to_datetime(pub_date_el.text)
                except Exception:
                    start_time = datetime.now(tz=timezone.utc)
            else:
                start_time = datetime.now(tz=timezone.utc)

            # GDACS-specific fields
            event_type_code = item.findtext("gdacs:eventtype", namespaces=ns) or ""
            event_id = item.findtext("gdacs:eventid", namespaces=ns) or ""
            episode_id = item.findtext("gdacs:episodeid", namespaces=ns) or ""
            alert_level = (item.findtext("gdacs:alertlevel", namespaces=ns) or "green").lower()

            lat_text = item.findtext("geo:lat", namespaces=ns)
            lon_text = item.findtext("geo:long", namespaces=ns)
            lat = float(lat_text) if lat_text else None
            lon = float(lon_text) if lon_text else None

            event_type = _EVENT_TYPE_MAP.get(event_type_code.upper(), EventType.other)
            severity = _ALERT_SEVERITY.get(alert_level, 0.2)
            source_event_id = f"GDACS-{event_type_code}-{event_id}-{episode_id}" or str(uuid.uuid4())

            events.append(
                EventCreate(
                    source_id=self.source_id,
                    source_event_id=source_event_id,
                    event_type=event_type,
                    title=title or "GDACS Alert",
                    summary=summary or "",
                    url=url_str or "",
                    start_time=start_time,
                    lat=lat,
                    lon=lon,
                    severity=severity,
                    tags=["gdacs", alert_level, event_type_code.lower()],
                    raw_payload={
                        "title": title,
                        "link": url_str,
                        "alert_level": alert_level,
                        "event_type_code": event_type_code,
                    },
                )
            )
        logger.info("GDACS: fetched %d events", len(events))
        return events
