from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.message import Message
from app.schemas.message import MessageOut
from sqlalchemy import func, select
from typing import List

router = APIRouter(prefix="/messages", tags=["messages"])


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

    query = select(Message).where(Message.room_id == room_id)

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

    return messages[::-1]  # frontend gets message in [Oldest,......., Newest]


@router.get("/search", response_model=List[MessageOut])
async def search_messages(
    q: str = Query(..., min_length=1, description="Search query"),
    room_id: str = Query(..., description="Room to search in"),
    limit: int = Query(20, ge=1, le=50, description="Max results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Full-text search using PostgreSQL tsvector.
    - Searches both message content and username.
    - Results are ranked by relevance.
    """
    # Convert user query to tsquery format (handles stemming, stop words)
    query_obj = func.plainto_tsquery("english", q)

    # Build the search query
    stmt = (
        select(Message)
        .where(Message.room_id == room_id, Message.search_vector.op("@@")(query_obj))
        .order_by(func.ts_rank(Message.search_vector, query_obj).desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    messages = result.scalars().all()

    return messages
