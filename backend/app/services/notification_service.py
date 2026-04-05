from __future__ import annotations

import logging
import math
from typing import Any

from app.models.event import Event
from app.models.subscription import Subscription
from app.services.email_sender import send_email
from app.services.whatsapp_sender import send_whatsapp
from app.services.webpush_sender import send_webpush

logger = logging.getLogger(__name__)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in kilometres between two points."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _point_in_polygon(lat: float, lon: float, polygon_coords: list[list[float]]) -> bool:
    """Ray-casting point-in-polygon check. Coords are [lon, lat] GeoJSON style."""
    inside = False
    n = len(polygon_coords)
    j = n - 1
    for i in range(n):
        xi, yi = polygon_coords[i][0], polygon_coords[i][1]
        xj, yj = polygon_coords[j][0], polygon_coords[j][1]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-10) + xi):
            inside = not inside
        j = i
    return inside


def _matches_geo_fence(event: Event, geo_fence: dict[str, Any]) -> bool:
    """Return True if the event location is within the geo fence."""
    if event.lat is None or event.lon is None:
        return False

    fence_type = geo_fence.get("type", "")
    if fence_type == "circle":
        center_lat = geo_fence.get("lat", 0.0)
        center_lon = geo_fence.get("lon", 0.0)
        radius_km = geo_fence.get("radius_km", 0.0)
        dist = _haversine_km(event.lat, event.lon, center_lat, center_lon)
        return dist <= radius_km
    elif fence_type in ("Polygon", "polygon"):
        coords = geo_fence.get("coordinates", [[]])[0]
        return _point_in_polygon(event.lat, event.lon, coords)
    return False


def subscription_matches(sub: Subscription, event: Event) -> bool:
    """Determine whether a subscription's criteria match a given event."""
    if not sub.is_active:
        return False

    # Event type filter (empty list = all types)
    if sub.event_types and event.event_type.value not in sub.event_types:
        return False

    # Severity filter
    if event.severity is not None and event.severity < sub.min_severity:
        return False

    # Keyword filter (any keyword must appear in title or summary)
    if sub.keywords:
        text = f"{event.title} {event.summary}".lower()
        if not any(kw.lower() in text for kw in sub.keywords):
            return False

    # Geo fence check
    if sub.geo_fence:
        if not _matches_geo_fence(event, sub.geo_fence):
            return False

    return True


async def evaluate_and_notify(
    event: Event,
    subscriptions: list[Subscription],
    user_email_map: dict[str, str],
    user_phone_map: dict[str, str] | None = None,
) -> None:
    """Evaluate subscriptions against an event and dispatch notifications."""
    for sub in subscriptions:
        if not subscription_matches(sub, event):
            continue

        user_id_str = str(sub.user_id)
        subject = f"[World Monitor] {event.event_type.value.title()}: {event.title}"
        body = (
            f"<h2>{event.title}</h2>"
            f"<p><strong>Type:</strong> {event.event_type.value}</p>"
            f"<p><strong>Severity:</strong> {event.severity}</p>"
            f"<p><strong>Location:</strong> {event.country or 'Unknown'}, "
            f"{event.region or ''}</p>"
            f"<p>{event.summary}</p>"
            f"<p><a href='{event.url}'>View details</a></p>"
        )

        if sub.notify_email and user_id_str in user_email_map:
            try:
                await send_email(user_email_map[user_id_str], subject, body)
            except Exception as exc:
                logger.error("Email notification failed for sub %s: %s", sub.id, exc)

        if sub.notify_whatsapp and user_phone_map and user_id_str in user_phone_map:
            plain = f"{event.event_type.value.title()}: {event.title} | {event.url}"
            try:
                await send_whatsapp(user_phone_map[user_id_str], plain)
            except Exception as exc:
                logger.error("WhatsApp notification failed for sub %s: %s", sub.id, exc)

        if sub.notify_webpush:
            send_webpush(user_id_str, subject, event.summary or event.title)
