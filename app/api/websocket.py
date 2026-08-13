from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..core.security import get_user_from_token
from ..models.user import User
from ..models.message import Message
from ..schemas.message import MessageCreate
from ..core.redis import get_redis
import json
import asyncio

router = APIRouter()

# We'll manage active connections per room in a dictionary:
# room_id -> set of WebSocket objects
active_connections: dict[str, set[WebSocket]] = {}


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
):
    # Authenticate via query param token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    # Get a DB session for auth
    async for db in get_db():
        current_user = await get_user_from_token(token, db)
        break
    else:
        await websocket.close(code=1008)
        return

    if not current_user:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    # Add to room connections
    if room_id not in active_connections:
        active_connections[room_id] = set()
    active_connections[room_id].add(websocket)

    # Get redis and DB for message handling
    redis = await get_redis()

    # Subscribe to Redis channel for this room (to receive messages from other instances)
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"chat:{room_id}")

    # Task that listens to Redis and forwards to WebSocket
    async def redis_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    # data is JSON string
                    await websocket.send_text(data)
        except asyncio.CancelledError:
            pass

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            # Wait for message from this client
            raw = await websocket.receive_text()
            try:
                msg_data = json.loads(raw)
                content = msg_data.get("content")
                if not content:
                    continue
                # Save to DB
                async for db in get_db():
                    new_msg = Message(
                        content=content, user_id=current_user.id, room_id=room_id
                    )
                    db.add(new_msg)
                    await db.commit()
                    await db.refresh(new_msg)
                    # Prepare payload for broadcasting
                    payload = {
                        "id": new_msg.id,
                        "content": new_msg.content,
                        "user_id": new_msg.user_id,
                        "room_id": new_msg.room_id,
                        "created_at": new_msg.created_at.isoformat(),
                    }
                    break
                payload_json = json.dumps(payload)
                # Broadcast to all WebSocket connections in this room (local)
                for conn in active_connections.get(room_id, set()):
                    try:
                        await conn.send_text(payload_json)
                    except Exception:
                        pass
                # Publish to Redis so other instances also broadcast
                await redis.publish(f"chat:{room_id}", payload_json)
            except json.JSONDecodeError:
                continue
    except WebSocketDisconnect:
        # Remove from active connections
        active_connections.get(room_id, set()).discard(websocket)
        if not active_connections.get(room_id):
            active_connections.pop(room_id, None)
        # Cancel listener task
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        await pubsub.unsubscribe(f"chat:{room_id}")
