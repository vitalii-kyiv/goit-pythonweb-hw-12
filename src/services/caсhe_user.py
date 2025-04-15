from datetime import datetime
import json
from src.conf.config import settings
import redis.asyncio as redis

redis_client = redis.from_url(settings.REDIS_URL)

async def cache_user(user, token: str, exp: int):
    """
    Cache the current user's data in Redis using the token as the key.

    Args:
        user: User object containing user details.
        token (str): Access token used as the Redis key.
        exp (int): Expiration timestamp of the token to calculate TTL.

    The user data will be cached until the token expires to optimize
    retrieval of the currently authenticated user.
    """
    ttl = int(exp - datetime.now().timestamp())
    key = f"user:{token}"
    user_data = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "avatar": user.avatar,
        "confirmed": user.confirmed
    }
    await redis_client.setex(key, ttl, json.dumps(user_data))
