"""
Redis Caching Service
Caches expensive database queries to reduce load
"""

import json
import os
from typing import Optional, Any, Callable
from functools import wraps
from datetime import timedelta

try:
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class CacheService:
    """Centralized caching service with Redis backend"""
    
    def __init__(self):
        self.enabled = REDIS_AVAILABLE and os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
        
        if self.enabled:
            try:
                self.redis = Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    db=int(os.getenv('REDIS_DB', 0)),
                    decode_responses=True,
                    socket_timeout=2,
                    socket_connect_timeout=2
                )
                # Test connection
                self.redis.ping()
                print("✅ Redis cache enabled")
            except Exception as e:
                print(f"⚠️  Redis connection failed: {e}. Caching disabled.")
                self.enabled = False
        else:
            print("ℹ️  Redis not available. Caching disabled.")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 600):
        """Set value in cache with TTL"""
        if not self.enabled:
            return
        
        try:
            self.redis.setex(
                key,
                ttl_seconds,
                json.dumps(value, default=str)  # default=str handles datetime
            )
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled:
            return
        
        try:
            self.redis.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if not self.enabled:
            return
        
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        except Exception as e:
            print(f"Cache clear error: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.redis.info()
            return {
                "enabled": True,
                "connected": True,
                "used_memory_mb": round(info['used_memory'] / 1024 / 1024, 2),
                "keys": self.redis.dbsize(),
                "hits": info.get('keyspace_hits', 0),
                "misses": info.get('keyspace_misses', 0),
                "hit_rate": round(
                    info.get('keyspace_hits', 0) / 
                    max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100,
                    2
                )
            }
        except Exception as e:
            return {"enabled": True, "connected": False, "error": str(e)}

# Global cache instance
cache = CacheService()


def cached(key_prefix: str, ttl_seconds: int = 600):
    """
    Decorator to cache function results
    
    Usage:
        @cached("invoice_stats", ttl_seconds=300)
        def get_invoice_statistics():
            # Expensive query
            return compute_stats()
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


# Specific cache helpers for common patterns

def cache_customer_summary(customer_id: int):
    """Cache key for customer summary"""
    return f"customer_summary:{customer_id}"

def cache_invoice_stats():
    """Cache key for invoice statistics"""
    return "invoice_stats:summary"

def cache_khata_summary(customer_id: int):
    """Cache key for khata summary"""
    return f"khata_summary:{customer_id}"

def cache_marketplace_stats():
    """Cache key for marketplace stats"""
    return "marketplace_stats:summary"

# Invalidation helpers

def invalidate_customer_cache(customer_id: int):
    """Invalidate all caches related to a customer"""
    cache.delete(cache_customer_summary(customer_id))
    cache.delete(cache_khata_summary(customer_id))

def invalidate_invoice_cache():
    """Invalidate invoice statistics cache"""
    cache.delete(cache_invoice_stats())

def invalidate_marketplace_cache():
    """Invalidate marketplace statistics cache"""
    cache.delete(cache_marketplace_stats())
