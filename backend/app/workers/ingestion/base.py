from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from app.schemas.event import EventCreate


class BaseIngestor(ABC):
    """Abstract base class for event ingestors."""

    @abstractmethod
    async def fetch(self) -> List[EventCreate]:
        """Fetch events from the source and return a list of EventCreate objects."""
        ...
