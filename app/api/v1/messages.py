from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...models.message import Message
from ...schemas.message import MessageOut
from ...core.security import get_current_user
from ...models.user import User

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/{room_id}", response_model=list[MessageOut])
async def get_message_history(
    room_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Message)
        .where(Message.room_id == room_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return messages[::-1]  # return in chronological order
