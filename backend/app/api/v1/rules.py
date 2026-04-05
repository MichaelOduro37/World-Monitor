from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_admin
from app.database import get_db
from app.models.rule import Rule
from app.models.user import User
from app.schemas.rule import RuleCreate, RuleResponse, RuleUpdate

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("", response_model=list[RuleResponse])
async def list_rules(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[Rule]:
    result = await db.execute(select(Rule).order_by(Rule.created_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: RuleCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Rule:
    rule = Rule(id=uuid.uuid4(), created_by=admin.id, **payload.model_dump())
    db.add(rule)
    await db.flush()
    return rule


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: uuid.UUID,
    payload: RuleUpdate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Rule:
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalars().first()
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(rule, field, value)
    db.add(rule)
    await db.flush()
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def delete_rule(
    rule_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalars().first()
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    await db.delete(rule)
