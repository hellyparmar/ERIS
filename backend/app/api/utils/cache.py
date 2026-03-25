"""
Redis Caching Utility
FastAPI dependency and decorator for caching JSON responses
"""

import os
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional
from fastapi import Request, Response
from redis import from_url, ConnectionError

logger = logging.getLogger(__name__)

# Initialize Redis client globally
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = None

try:
    redis_client = from_url(REDIS_URL, decode_responses=True, socket_timeout=2.0)
    # Test connection
    redis_client.ping()
    logger.info("Successfully connected to Redis for caching.")
except ConnectionError:
    logger.warning("Redis is not accessible. Caching is disabled.")
    redis_client = None
except Exception as e:
    logger.warning(f"Failed to initialize Redis cache: {e}")
    redis_client = None


def cache_response(ttl_seconds: int = 300):
    """
    Decorator to cache endpoint responses in Redis.
    Uses request path and query params as the cache key.
    If Redis is down, smoothly falls back to executing the function.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not redis_client:
                return await func(*args, **kwargs)
                
            # Find the Request object to build the cache key
            request: Optional[Request] = kwargs.get('request')
            if not request:
                # Search *args just in case
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            # If no request object passed, we can't reliably cache by URL, so bypass
            if not request:
                return await func(*args, **kwargs)
                
            # Construct cache key from path and query string
            key = f"cache:{request.url.path}"
            if request.url.query:
                key += f"?{request.url.query}"
                
            try:
                cached_data = redis_client.get(key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                
            # Execute the endpoint
            response_data = await func(*args, **kwargs)
            
            try:
                # Save to cache
                if isinstance(response_data, dict) or isinstance(response_data, list):
                    redis_client.setex(key, ttl_seconds, json.dumps(response_data))
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                
            return response_data
            
        return wrapper
    return decorator
