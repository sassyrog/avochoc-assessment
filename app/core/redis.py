import logging
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def check_redis_connection():
    """Test Redis connection"""
    try:
        await redis_client.ping()
        logger.info("redis connected")
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False
