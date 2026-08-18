import redis.asyncio as aioredis
from .config import settings

redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

async def add_user_to_room(room_id: str, username: str):
    await redis_client.sadd(f"chat:room:{room_id}:users", username)

async def remove_user_from_room(room_id: str, username: str):
    await redis_client.srem(f"chat:room:{room_id}:users", username)

async def get_room_users(room_id: str) -> set:
    return await redis_client.smembers(f"chat:room:{room_id}:users")

async def get_redis():
    return redis_client

