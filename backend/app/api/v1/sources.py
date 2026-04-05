from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_admin
from app.database import get_db
from app.models.source import Source
from app.models.user import User
from app.schemas.source import SourceCreate, SourceResponse, SourceUpdate

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceResponse])
async def list_sources(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[Source]:
    result = await db.execute(select(Source).order_by(Source.name))
    return list(result.scalars().all())


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: SourceCreate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Source:
    existing = await db.execute(select(Source).where(Source.name == payload.name))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Source name already exists"
        )
    source = Source(id=uuid.uuid4(), **payload.model_dump())
    db.add(source)
    await db.flush()
    return source


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: uuid.UUID,
    payload: SourceUpdate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Source:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalars().first()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(source, field, value)
    db.add(source)
    await db.flush()
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def delete_source(
    source_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalars().first()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    await db.delete(source)


@router.post("/{source_id}/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_ingestion(
    source_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalars().first()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    try:
        from app.workers.tasks import ingest_source

        ingest_source.delay(str(source_id))
    except Exception:
        pass
    return {"detail": "Ingestion triggered", "source_id": str(source_id)}
