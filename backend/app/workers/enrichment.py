from __future__ import annotations

import logging
import time
from typing import Optional

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError

logger = logging.getLogger(__name__)

_geolocator = Nominatim(user_agent="world-monitor-enrichment/1.0")


def reverse_geocode(lat: float, lon: float) -> tuple[str | None, str | None]:
    """Return (country, region) for a lat/lon pair using Nominatim.

    Sleeps 1 second between requests to comply with Nominatim ToS.
    Returns (None, None) on failure.
    """
    try:
        time.sleep(1)  # Nominatim rate-limit: max 1 req/sec
        location = _geolocator.reverse(
            (lat, lon), exactly_one=True, language="en", timeout=10
        )
        if location is None:
            return None, None
        address = location.raw.get("address", {})
        country = address.get("country")
        region = (
            address.get("state")
            or address.get("region")
            or address.get("county")
        )
        return country, region
    except (GeocoderServiceError, Exception) as exc:
        logger.warning("Reverse geocode failed for (%s, %s): %s", lat, lon, exc)
        return None, None


async def enrich_event_location(lat: Optional[float], lon: Optional[float]) -> tuple[str | None, str | None]:
    """Async wrapper around reverse_geocode (runs in executor)."""
    if lat is None or lon is None:
        return None, None
    import asyncio

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, reverse_geocode, lat, lon)
