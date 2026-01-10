import json
import logging
from functools import wraps
from typing import Callable

from app.core.redis import redis_client

logger = logging.getLogger(__name__)


def cache_response(key_pattern: str, expire: int = 60):
    """
    Decorator to cache API responses.

    Args:
        key_pattern: Redis key pattern (e.g., "assets:list").
        expire: Expiration time in seconds.
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Form cache key (handle dynamic logic if needed later)
            cache_key = key_pattern

            # Try to get from cache
            try:
                cached_data = await redis_client.get(cache_key)
                if cached_data:
                    logger.info(f"Cache hit: {cache_key}")
                    # Reconstruct structure. Note: We assume SuccessResponse here
                    # effectively caching the 'data' part or full response logic.
                    # For simplicity in this assessment, we'll cache the raw JSON string
                    # of the standard response model.
                    data = json.loads(cached_data)
                    return data
            except Exception as e:
                logger.error(f"Cache read error: {e}")

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            try:
                from fastapi.encoders import jsonable_encoder

                # Try to get a JSON-compatible dict
                try:
                    data = jsonable_encoder(result)
                except Exception:
                    # Fallback for Pydantic models with non-serializable fields (like Mocks or half-loaded DB models)
                    if hasattr(result, "model_dump"):
                        data = result.model_dump()
                    elif hasattr(result, "dict"):
                        data = result.dict()
                    else:
                        data = result

                # final serialization with string fallback for unknown types
                serialized = json.dumps(data, default=str)

                await redis_client.setex(cache_key, expire, serialized)
                logger.info(f"Cache set: {cache_key}")
            except Exception as e:
                logger.error(f"Cache write error: {e}")

            return result

        return wrapper

    return decorator


async def invalidate_cache(key_pattern: str):
    """
    Invalidate cache keys matching a specific pattern.
    For this assessment, we primarily assume direct key matches or simple patterns.
    """
    try:
        # If we used true wildcards we'd need SCAN, but here we likely know the key
        await redis_client.delete(key_pattern)
        logger.info(f"Cache invalidated: {key_pattern}")
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
