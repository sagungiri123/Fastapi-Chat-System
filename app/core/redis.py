import redis.asyncio as aioredis
from .config import settings

redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_redis():
    return redis_client
