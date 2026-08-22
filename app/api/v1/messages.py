import json
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.redis import get_redis
from app.models.user import User
from app.models.message import Message
from app.schemas.message import MessageOut
from pydantic import BaseModel

router = APIRouter(prefix="/messages", tags=["messages"])


# ---------- PAGINATION ENDPOINT ----------
@router.get("/{room_id}", response_model=list[MessageOut])
async def get_message_history(
    room_id: str,
    limit: int = Query(20, ge=1, le=100, description="Number of messages to load"),
    before_id: int = Query(
        None, description="Cursor: Load messages older than this ID"
    ),
    before_timestamp: datetime = Query(
        None, description="Cursor: Load messages older than this timestamp"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Message).where(
        Message.room_id == room_id,
        Message.deleted_at.is_(None),  # Exclude soft-deleted messages
    )

    if before_id is not None and before_timestamp is not None:
        query = query.where(
            or_(
                Message.created_at < before_timestamp,
                and_(Message.created_at == before_timestamp, Message.id < before_id),
            )
        )

    query = query.order_by(desc(Message.created_at), desc(Message.id)).limit(limit)

    result = await db.execute(query)
    messages = result.scalars().all()

    return messages[::-1]  # Oldest → Newest


# ---------- SEARCH ENDPOINT ----------
@router.get("/search", response_model=List[MessageOut])
async def search_messages(
    q: str = Query(..., min_length=1, description="Search query"),
    room_id: str = Query(..., description="Room to search in"),
    limit: int = Query(20, ge=1, le=50, description="Max results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query_obj = func.plainto_tsquery("english", q)

    stmt = (
        select(Message)
        .where(
            Message.room_id == room_id,
            Message.deleted_at.is_(None),  # Exclude soft-deleted messages
            Message.search_vector.op("@@")(query_obj),
        )
        .order_by(func.ts_rank(Message.search_vector, query_obj).desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    messages = result.scalars().all()

    return messages


# ---------- EDIT ENDPOINT ----------
class MessageUpdate(BaseModel):
    content: str


@router.patch("/{message_id}")
async def edit_message(
    message_id: int,
    update: MessageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Fetch the message (exclude deleted)
    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.deleted_at.is_(None))
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Authorization: Only the sender can edit
    if message.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to edit this message"
        )

    # Update content
    message.content = update.content
    message.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(message)

    # ---------- BROADCAST EDIT VIA REDIS ----------
    payload = {
        "type": "edit",
        "message_id": message.id,
        "content": message.content,
        "updated_at": message.updated_at.isoformat() if message.updated_at else None,
    }
    payload_json = json.dumps(payload)

    redis = await get_redis()
    await redis.publish(f"chat:{message.room_id}", payload_json)

    return message


# ---------- DELETE ENDPOINT (Soft Delete) ----------
@router.delete("/{message_id}")
async def delete_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Fetch the message (exclude already deleted)
    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.deleted_at.is_(None))
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Authorization: Only the sender can delete
    if message.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this message"
        )

    # Soft delete
    message.deleted_at = datetime.utcnow()
    await db.commit()

    # ---------- BROADCAST DELETE VIA REDIS ----------
    payload = {
        "type": "delete",
        "message_id": message.id,
    }
    payload_json = json.dumps(payload)

    redis = await get_redis()
    await redis.publish(f"chat:{message.room_id}", payload_json)

    return {"message": "Message deleted successfully"}
