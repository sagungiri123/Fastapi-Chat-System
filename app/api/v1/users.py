from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import UserOut  # We already have this

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/search", response_model=list[UserOut])
async def search_users(
    username: str = Query(..., min_length=1, description="Username to search for"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Must be logged in
):
    # Search for users whose username contains the query (case insensitive)
    # Exclude the current user from the results (so Alice doesn't find herself)
    result = await db.execute(
        select(User)
        .where(User.username.ilike(f"%{username}%"))
        .where(User.id != current_user.id)
        .limit(10)
    )
    users = result.scalars().all()
    return users

@router.get("/{target_user_id}/dm_room")
async def get_dm_room(
    target_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify the target user exists
    result = await db.execute(select(User).where(User.id == target_user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 2. Deterministic room naming
    ids = sorted([current_user.id, target_user_id])
    room_id = f"dm_{ids[0]}_{ids[1]}"
    
    return {"room_id": room_id}