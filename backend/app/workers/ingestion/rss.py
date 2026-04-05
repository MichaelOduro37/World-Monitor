from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List

import feedparser

from app.models.event import EventType
from app.schemas.event import EventCreate
from app.workers.ingestion.base import BaseIngestor

logger = logging.getLogger(__name__)


class RSSIngestor(BaseIngestor):
    """Generic RSS/Atom feed ingestor using feedparser."""

    def __init__(
        self,
        feed_url: str,
        source_id: uuid.UUID | None = None,
        default_event_type: EventType = EventType.news,
    ) -> None:
        self.feed_url = feed_url
        self.source_id = source_id
        self.default_event_type = default_event_type

    async def fetch(self) -> List[EventCreate]:
        try:
            # feedparser is synchronous; run it in a thread pool for async compat
            import asyncio

            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, self.feed_url)
        except Exception as exc:
            logger.error("RSS fetch failed for %s: %s", self.feed_url, exc)
            return []

        if feed.bozo and not feed.entries:
            logger.warning("RSS feed %s returned bozo=True with no entries", self.feed_url)
            return []

        events: List[EventCreate] = []
        for entry in feed.entries:
            source_event_id = getattr(entry, "id", None) or getattr(entry, "link", None)
            if not source_event_id:
                source_event_id = str(uuid.uuid4())

            title = getattr(entry, "title", "")
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            url_str = getattr(entry, "link", "")

            # Parse published date
            published_parsed = getattr(entry, "published_parsed", None)
            updated_parsed = getattr(entry, "updated_parsed", None)
            if published_parsed:
                import time

                start_time = datetime.fromtimestamp(
                    time.mktime(published_parsed), tz=timezone.utc
                )
            else:
                start_time = datetime.now(tz=timezone.utc)

            updated_time: datetime | None = None
            if updated_parsed:
                import time

                updated_time = datetime.fromtimestamp(
                    time.mktime(updated_parsed), tz=timezone.utc
                )

            tags = [t.get("term", "") for t in getattr(entry, "tags", []) if t.get("term")]

            events.append(
                EventCreate(
                    source_id=self.source_id,
                    source_event_id=source_event_id,
                    event_type=self.default_event_type,
                    title=title,
                    summary=summary,
                    url=url_str,
                    start_time=start_time,
                    updated_time=updated_time,
                    tags=tags,
                    raw_payload={
                        "title": title,
                        "link": url_str,
                        "summary": summary,
                        "source_feed": self.feed_url,
                    },
                )
            )

        logger.info("RSS %s: fetched %d entries", self.feed_url, len(events))
        return events
