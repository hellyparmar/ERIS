"""
Redis Cache Service for R-DIOS
Prevents repeated expensive queries (dashboard metrics scanning 424K rows)
"""

import redis
import json
import logging
import os
from functools import wraps
from typing import Any, Optional, Callable

logger = logging.getLogger(__name__)

# Connect to Redis
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

try:
    cache_client = redis.from_url(REDIS_URL, decode_responses=True)
    cache_client.ping()
    logger.info("✓ Redis cache connected")
except Exception as e:
    logger.error(f"Redis connection failed: {e} — falling back to no cache")
    cache_client = None

class CacheService:
    """Redis-based caching service"""
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache"""
        if not cache_client:
            return None
        try:
            value = cache_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache GET error: {e}")
        return None
    
    @staticmethod
    def set(key: str, value: Any, ttl_seconds: int = 60) -> bool:
        """Set value in cache with TTL"""
        if not cache_client:
            return False
        try:
            cache_client.setex(key, ttl_seconds, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.error(f"Cache SET error: {e}")
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """Delete from cache"""
        if not cache_client:
            return False
        try:
            cache_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache DELETE error: {e}")
            return False
    
    @staticmethod
    def clear_pattern(pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not cache_client:
            return 0
        try:
            keys = cache_client.keys(pattern)
            if keys:
                return cache_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache CLEAR error: {e}")
        return 0

def cache(key_prefix: str, ttl_seconds: int = 60):
    """Decorator for caching function results"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Build cache key
            args_str = str(args).replace(" ", "")
            kwargs_str = str(sorted(kwargs.items())).replace(" ", "")
            cache_key = f"{key_prefix}:{hash(args_str + kwargs_str)}"
            
            # Try to get from cache
            cached = CacheService.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            CacheService.set(cache_key, result, ttl_seconds)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            args_str = str(args).replace(" ", "")
            kwargs_str = str(sorted(kwargs.items())).replace(" ", "")
            cache_key = f"{key_prefix}:{hash(args_str + kwargs_str)}"
            
            cached = CacheService.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
            
            result = func(*args, **kwargs)
            CacheService.set(cache_key, result, ttl_seconds)
            return result
        
        # Return async or sync wrapper based on function
        if hasattr(func, '__await__'):
            return async_wrapper
        return sync_wrapper
    
    return decorator

# Pre-built cache keys for common use cases
class CacheKeys:
    """Standard cache key patterns"""
    DASHBOARD_METRICS = "dashboard:metrics"
    INVENTORY_LIST = "inventory:list"
    PRODUCTS_LIST = "products:list"
    ALERTS_LIST = "alerts:list"
    SALES_SUMMARY = "sales:summary"
    FORECAST = "forecast"
    FORECAST_ACCURACY = "forecast:accuracy"
