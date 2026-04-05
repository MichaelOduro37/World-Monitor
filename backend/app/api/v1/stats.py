from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event, EventType

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary")
async def get_summary(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return aggregate statistics for the events collection."""
    now = datetime.now(tz=timezone.utc)
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)

    # Total count
    total_result = await db.execute(select(func.count()).select_from(Event))
    total: int = total_result.scalar_one()

    # Last 24h / 7d / 30d counts
    count_24h_result = await db.execute(
        select(func.count()).select_from(Event).where(Event.start_time >= last_24h)
    )
    count_24h: int = count_24h_result.scalar_one()

    count_7d_result = await db.execute(
        select(func.count()).select_from(Event).where(Event.start_time >= last_7d)
    )
    count_7d: int = count_7d_result.scalar_one()

    count_30d_result = await db.execute(
        select(func.count()).select_from(Event).where(Event.start_time >= last_30d)
    )
    count_30d: int = count_30d_result.scalar_one()

    # Counts by event type (all time)
    type_rows = await db.execute(
        select(Event.event_type, func.count().label("cnt"))
        .group_by(Event.event_type)
        .order_by(func.count().desc())
    )
    by_type = {row.event_type: row.cnt for row in type_rows}

    # Counts by event type in last 24h
    type_24h_rows = await db.execute(
        select(Event.event_type, func.count().label("cnt"))
        .where(Event.start_time >= last_24h)
        .group_by(Event.event_type)
        .order_by(func.count().desc())
    )
    by_type_24h = {row.event_type: row.cnt for row in type_24h_rows}

    # Severity distribution (all time, non-null severity)
    severity_result = await db.execute(
        select(
            func.sum(case((Event.severity >= 0.75, 1), else_=0)).label("critical"),
            func.sum(case((and_(Event.severity >= 0.5, Event.severity < 0.75), 1), else_=0)).label("high"),
            func.sum(case((and_(Event.severity >= 0.25, Event.severity < 0.5), 1), else_=0)).label("medium"),
            func.sum(case((and_(Event.severity >= 0.0, Event.severity < 0.25), 1), else_=0)).label("low"),
            func.sum(case((Event.severity.is_(None), 1), else_=0)).label("unknown"),
        ).select_from(Event)
    )
    sev_row = severity_result.one()
    by_severity = {
        "critical": sev_row.critical or 0,
        "high": sev_row.high or 0,
        "medium": sev_row.medium or 0,
        "low": sev_row.low or 0,
        "unknown": sev_row.unknown or 0,
    }

    # Duplicate stats
    dup_result = await db.execute(
        select(func.count()).select_from(Event).where(Event.is_duplicate.is_(True))
    )
    duplicate_count: int = dup_result.scalar_one()

    return {
        "total": total,
        "last_24h": count_24h,
        "last_7d": count_7d,
        "last_30d": count_30d,
        "by_type": by_type,
        "by_type_24h": by_type_24h,
        "by_severity": by_severity,
        "duplicate_count": duplicate_count,
        "generated_at": now.isoformat(),
    }


@router.get("/hotspots")
async def get_hotspots(
    days: int = Query(default=7, ge=1, le=90, description="Lookback window in days"),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return top countries and regions by event count within the lookback window."""
    since = datetime.now(tz=timezone.utc) - timedelta(days=days)

    country_rows = await db.execute(
        select(Event.country, func.count().label("cnt"))
        .where(
            and_(
                Event.start_time >= since,
                Event.country.is_not(None),
            )
        )
        .group_by(Event.country)
        .order_by(func.count().desc())
        .limit(limit)
    )
    top_countries = [
        {"country": row.country, "count": row.cnt} for row in country_rows
    ]

    region_rows = await db.execute(
        select(Event.country, Event.region, func.count().label("cnt"))
        .where(
            and_(
                Event.start_time >= since,
                Event.region.is_not(None),
            )
        )
        .group_by(Event.country, Event.region)
        .order_by(func.count().desc())
        .limit(limit)
    )
    top_regions = [
        {"country": row.country, "region": row.region, "count": row.cnt}
        for row in region_rows
    ]

    return {
        "days": days,
        "top_countries": top_countries,
        "top_regions": top_regions,
    }
