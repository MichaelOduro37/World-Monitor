from __future__ import annotations

import logging
import smtplib

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send an HTML email. Returns True on success, False otherwise."""
    if not settings.SMTP_HOST:
        logger.warning(
            "SMTP_HOST not configured – skipping email to %s (subject: %s)", to, subject
        )
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            start_tls=settings.SMTP_PORT == 587,
        )
        logger.info("Email sent to %s: %s", to, subject)
        return True
    except (aiosmtplib.SMTPException, smtplib.SMTPException, OSError) as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return False
