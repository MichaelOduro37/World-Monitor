from __future__ import annotations

import json
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory registry for dev; in production replace with a DB-backed store.
_push_subscriptions: dict[str, dict[str, Any]] = {}


def register_push_subscription(user_id: str, subscription_info: dict[str, Any]) -> None:
    """Store a browser push subscription for a user."""
    _push_subscriptions[user_id] = subscription_info


def send_webpush(user_id: str, title: str, body: str) -> bool:
    """Send a web push notification.

    Returns True on success, False if VAPID keys are missing or subscription
    not found.
    """
    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        logger.warning(
            "VAPID keys not configured – skipping web push for user %s", user_id
        )
        return False

    subscription_info = _push_subscriptions.get(user_id)
    if not subscription_info:
        logger.debug("No push subscription registered for user %s", user_id)
        return False

    try:
        from pywebpush import webpush, WebPushException

        data = json.dumps({"title": title, "body": body})
        webpush(
            subscription_info=subscription_info,
            data=data,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": f"mailto:{settings.VAPID_CLAIMS_EMAIL}"},
        )
        logger.info("Web push sent to user %s", user_id)
        return True
    except Exception as exc:
        logger.error("Web push failed for user %s: %s", user_id, exc)
        return False
