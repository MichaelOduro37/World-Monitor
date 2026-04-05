from __future__ import annotations

import json
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://worldmonitor:worldmonitor@db:5432/worldmonitor"

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS – comma-separated list or JSON array of allowed origins (production)
    CORS_ORIGINS: List[str] = []

    # SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@worldmonitor.example.com"

    # WhatsApp Cloud API
    WHATSAPP_ENABLED: bool = False
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""

    # Web Push / VAPID
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_CLAIMS_EMAIL: str = "admin@worldmonitor.example.com"

    # RSS feeds ingested by default
    RSS_FEEDS: List[str] = [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ]

    # Ingestion
    INGESTION_INTERVAL_SECONDS: int = 300

    # Environment
    APP_ENV: str = "development"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def ensure_asyncpg_driver(cls, v: object) -> object:
        """Normalise DATABASE_URL so it always uses the asyncpg driver.

        Managed database providers (Render, Railway, Fly.io) typically return
        ``postgres://`` or ``postgresql://`` without the driver suffix, which
        asyncpg requires.
        """
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return "postgresql+asyncpg://" + v[len("postgres://"):]
            if v.startswith("postgresql://"):
                return "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> object:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("RSS_FEEDS", mode="before")
    @classmethod
    def parse_rss_feeds(cls, v: object) -> object:
        """Accept RSS_FEEDS as a JSON array string or a Python list."""
        if isinstance(v, str):
            return json.loads(v)
        return v


settings = Settings()
