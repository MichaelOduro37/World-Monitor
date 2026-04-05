from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.deps import get_current_active_user
from app.models.user import User, UserRole


async def require_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Require an authenticated, active user (any role)."""
    return current_user


async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require an authenticated, active admin user."""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
