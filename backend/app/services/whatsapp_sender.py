from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = (
    "https://graph.facebook.com/v19.0/{phone_number_id}/messages"
)


async def send_whatsapp(to_number: str, message: str) -> bool:
    """Send a WhatsApp text message.

    If WHATSAPP_ENABLED is False the message is only logged (mock mode).
    """
    if not settings.WHATSAPP_ENABLED:
        logger.info(
            "[WhatsApp MOCK] to=%s | message=%s", to_number, message
        )
        return True

    url = WHATSAPP_API_URL.format(phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID)
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message},
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info("WhatsApp message sent to %s", to_number)
            return True
    except httpx.HTTPError as exc:
        logger.error("Failed to send WhatsApp message to %s: %s", to_number, exc)
        return False
