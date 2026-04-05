from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_active_user
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[Subscription]:
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    return list(result.scalars().all())


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Subscription:
    sub = Subscription(
        id=uuid.uuid4(),
        user_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(sub)
    await db.flush()
    return sub


@router.get("/{sub_id}", response_model=SubscriptionResponse)
async def get_subscription(
    sub_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Subscription:
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == sub_id, Subscription.user_id == current_user.id
        )
    )
    sub = result.scalars().first()
    if sub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return sub


@router.put("/{sub_id}", response_model=SubscriptionResponse)
async def update_subscription(
    sub_id: uuid.UUID,
    payload: SubscriptionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Subscription:
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == sub_id, Subscription.user_id == current_user.id
        )
    )
    sub = result.scalars().first()
    if sub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(sub, field, value)
    db.add(sub)
    await db.flush()
    return sub


@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def delete_subscription(
    sub_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == sub_id, Subscription.user_id == current_user.id
        )
    )
    sub = result.scalars().first()
    if sub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    await db.delete(sub)
