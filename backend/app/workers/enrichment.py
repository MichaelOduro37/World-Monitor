from __future__ import annotations

import logging
from typing import Optional

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError

logger = logging.getLogger(__name__)

_geolocator = Nominatim(user_agent="world-monitor-enrichment/1.0")


def reverse_geocode(lat: float, lon: float) -> tuple[str | None, str | None]:
    """Return (country, region) for a lat/lon pair using Nominatim.

    This is a synchronous function intended to be run in a thread-pool executor.
    Returns (None, None) on failure.
    """
    try:
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
    """Reverse-geocode a lat/lon pair, rate-limited to 1 req/sec per Nominatim ToS."""
    if lat is None or lon is None:
        return None, None
    import asyncio

    # Rate-limit: Nominatim ToS requires max 1 request per second
    await asyncio.sleep(1)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, reverse_geocode, lat, lon)
