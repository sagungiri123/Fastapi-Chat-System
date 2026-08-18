
from ..core.redis import (
    get_redis,
    add_user_to_room,
    remove_user_from_room,
    get_room_users,
)
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
import uuid

router = APIRouter()

# Unique id for this server process so we can avoid rebroadcasting our own Redis messages
SERVER_ID = uuid.uuid4().hex

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
    if room_id.startswith("dm_"):
        parts = room_id.split("_")
        if len(parts) == 3:
            try:
                user1, user2 = int(parts[1]), int(parts[2])
            except ValueError:
                await websocket.close(code=1008, reason="Invalid room format")
                return

            # Check if the authenticated user is one of the two participants
            if current_user.id not in (user1, user2):
                await websocket.close(code=1008, reason="Not authorized for this DM")
                return
        else:
            await websocket.close(code=1008, reason="Invalid DM room format")
            return

    await websocket.accept()

    await add_user_to_room(room_id, current_user.username)

    active_users = await get_room_users(room_id)

    list_payload = {
        "type": "online_list",
        "users": list(active_users),
        "origin": SERVER_ID,
    }
    list_payload_json = json.dumps(list_payload)

    # Ensure we have a redis client before publishing
    redis = await get_redis()

    # Send the online list to other local connections
    for conn in active_connections.get(room_id, set()):
        try:
            await conn.send_text(list_payload_json)
        except Exception:
            pass

    # Also send to the newly connected websocket so it sees the current list
    try:
        await websocket.send_text(list_payload_json)
    except Exception:
        pass

    # Publish the updated list to Redis for other instances
    await redis.publish(f"chat:{room_id}", list_payload_json)

    # Add to room connections
    if room_id not in active_connections:
        active_connections[room_id] = set()
    active_connections[room_id].add(websocket)

    # Get DB for message handling (redis client already acquired above)

    # Subscribe to Redis channel for this room (to receive messages from other instances)
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"chat:{room_id}")

    # Task that listens to Redis and forwards to WebSocket
    async def redis_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    # data is JSON string or bytes
                    try:
                        if isinstance(data, bytes):
                            data = data.decode()
                        parsed = json.loads(data)
                    except Exception:
                        # Not JSON; forward as-is
                        await websocket.send_text(data)
                        continue

                    # Skip messages that originated from this server instance
                    if parsed.get("origin") == SERVER_ID:
                        continue

                    # Forward the original JSON string to the websocket
                    await websocket.send_text(json.dumps(parsed))
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
                            "type": "message",
                            "id": new_msg.id,
                            "content": new_msg.content,
                            "user_id": new_msg.user_id,
                            "username": current_user.username,
                            "room_id": new_msg.room_id,
                            "created_at": new_msg.created_at.isoformat(),
                            "origin": SERVER_ID,
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
        
        await remove_user_from_room(room_id, current_user.username)
        
        active_users = await get_room_users(room_id)
        
        if active_users:
            list_payload = {
                'type': 'online_list',
                'users': list(active_users),
                'origin': SERVER_ID,
            }
            list_payload_json = json.dumps(list_payload)

            for conn in active_connections.get(room_id, set()):
                try:
                    await conn.send_text(list_payload_json)
                except :
                        pass
                    
            await redis.publish(f"chat:{room_id}", list_payload_json)
            