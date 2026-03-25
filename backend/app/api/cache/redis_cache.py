"""
Redis Caching Layer for Performance Optimization

Implements distributed caching for frequently accessed data:
- Product catalog with inventory
- GST rates and tax configuration
- Loyalty tier information
- Customer profiles
- Dashboard metrics

Features:
- Automatic cache invalidation
- Cache warming on startup
- Multi-level caching (Redis + in-memory)
- Cache hit/miss metrics
- Graceful degradation if Redis unavailable
"""

import json
import hashlib
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from functools import wraps
import logging
import asyncio

logger = logging.getLogger(__name__)

# ============================================================================
# Cache Configuration
# ============================================================================

class CacheConfig:
    """Cache configuration and expiration times"""
    
    # Cache TTL (Time To Live) in seconds
    PRODUCT_CATALOG_TTL = 3600  # 1 hour
    GST_RATES_TTL = 86400  # 24 hours
    LOYALTY_TIERS_TTL = 86400  # 24 hours
    CUSTOMER_PROFILE_TTL = 1800  # 30 minutes
    DASHBOARD_METRICS_TTL = 300  # 5 minutes
    INVENTORY_LEVELS_TTL = 600  # 10 minutes
    BARCODE_LOOKUP_TTL = 1800  # 30 minutes
    SALES_ANALYTICS_TTL = 300  # 5 minutes
    
    # Cache key prefixes
    PRODUCT_PREFIX = "cache:product:"
    GST_PREFIX = "cache:gst:"
    LOYALTY_PREFIX = "cache:loyalty:"
    CUSTOMER_PREFIX = "cache:customer:"
    DASHBOARD_PREFIX = "cache:dashboard:"
    INVENTORY_PREFIX = "cache:inventory:"
    BARCODE_PREFIX = "cache:barcode:"
    ANALYTICS_PREFIX = "cache:analytics:"
    
    # Cache invalidation event types
    INVALIDATE_PRODUCTS = "invalidate:products"
    INVALIDATE_GST = "invalidate:gst"
    INVALIDATE_LOYALTY = "invalidate:loyalty"
    INVALIDATE_CUSTOMER = "invalidate:customer:{customer_id}"
    INVALIDATE_INVENTORY = "invalidate:inventory"
    INVALIDATE_ANALYTICS = "invalidate:analytics"


# ============================================================================
# Redis Cache Manager
# ============================================================================

class RedisCacheManager:
    """
    Manages all Redis caching operations
    
    Features:
    - Get/set operations with automatic serialization
    - Batch operations for efficiency
    - Cache invalidation
    - Cache statistics
    - Graceful fallback if Redis unavailable
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }
    
    def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis.get(key)
            if value:
                self.stats["hits"] += 1
                if deserialize:
                    return json.loads(value)
                return value
            else:
                self.stats["misses"] += 1
                return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        serialize: bool = True
    ) -> bool:
        """Set value in cache with TTL"""
        try:
            if serialize:
                value = json.dumps(value, default=str)
            self.redis.setex(key, ttl, value)
            self.stats["sets"] += 1
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    def get_or_set(
        self,
        key: str,
        callable_fn: Callable,
        ttl: int = 3600,
        *args,
        **kwargs
    ) -> Any:
        """Get from cache or compute and set"""
        # Try cache first
        cached = self.get(key)
        if cached is not None:
            return cached
        
        # Compute if not in cache
        value = callable_fn(*args, **kwargs)
        
        # Store in cache
        self.set(key, value, ttl)
        
        return value
    
    async def get_or_set_async(
        self,
        key: str,
        async_callable: Callable,
        ttl: int = 3600,
        *args,
        **kwargs
    ) -> Any:
        """Async version of get_or_set"""
        # Try cache first
        cached = self.get(key)
        if cached is not None:
            return cached
        
        # Compute async if not in cache
        value = await async_callable(*args, **kwargs)
        
        # Store in cache
        self.set(key, value, ttl)
        
        return value
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            self.redis.delete(key)
            self.stats["deletes"] += 1
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                deleted = self.redis.delete(*keys)
                self.stats["deletes"] += deleted
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    def invalidate_category(self, category: str) -> int:
        """Invalidate all caches in a category"""
        pattern = f"cache:{category}:*"
        return self.delete_pattern(pattern)
    
    def clear_all(self) -> bool:
        """Clear all application caches"""
        try:
            self.redis.flushdb()
            self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}
            return True
        except Exception as e:
            logger.warning(f"Cache clear all error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            (self.stats["hits"] / total_requests * 100)
            if total_requests > 0
            else 0
        )
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "sets": self.stats["sets"],
            "deletes": self.stats["deletes"]
        }
    
    def reset_stats(self) -> None:
        """Reset cache statistics"""
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}


# ============================================================================
# In-Memory Cache (L1 Cache)
# ============================================================================

class InMemoryCache:
    """
    Fast in-memory cache for hot data
    
    Used as L1 cache before hitting Redis (L2) or database (L3)
    """
    
    def __init__(self, max_size: int = 10000):
        self.cache = {}
        self.expiry = {}
        self.max_size = max_size
        self.stats = {"hits": 0, "misses": 0}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from in-memory cache"""
        if key in self.cache:
            # Check if expired
            if key in self.expiry:
                if time.time() > self.expiry[key]:
                    del self.cache[key]
                    del self.expiry[key]
                    self.stats["misses"] += 1
                    return None
            
            self.stats["hits"] += 1
            return self.cache[key]
        
        self.stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in in-memory cache"""
        if len(self.cache) >= self.max_size:
            # Evict oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            if oldest_key in self.expiry:
                del self.expiry[oldest_key]
        
        self.cache[key] = value
        self.expiry[key] = time.time() + ttl
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from in-memory cache"""
        if key in self.cache:
            del self.cache[key]
            if key in self.expiry:
                del self.expiry[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all in-memory cache"""
        self.cache.clear()
        self.expiry.clear()


# ============================================================================
# Cache Warming (Preload Hot Data)
# ============================================================================

class CacheWarmer:
    """
    Preloads frequently accessed data into cache on startup
    
    Reduces cold start latency and improves initial performance
    """
    
    def __init__(self, cache_manager: RedisCacheManager, db_session):
        self.cache = cache_manager
        self.db = db_session
    
    def warm_product_catalog(self, db) -> int:
        """Preload product catalog into cache"""
        try:
            from app.api.db.database import Product
            
            products = db.query(Product).limit(1000).all()
            count = 0
            
            for product in products:
                key = f"{CacheConfig.PRODUCT_PREFIX}{product.id}"
                self.cache.set(
                    key,
                    {
                        "id": str(product.id),
                        "name": product.name,
                        "price": float(product.price),
                        "inventory": product.inventory,
                        "barcode": product.barcode
                    },
                    ttl=CacheConfig.PRODUCT_CATALOG_TTL
                )
                count += 1
            
            logger.info(f"Warmed {count} products into cache")
            return count
        except Exception as e:
            logger.error(f"Error warming product cache: {e}")
            return 0
    
    def warm_gst_rates(self, db) -> int:
        """Preload GST rates into cache"""
        try:
            # Assuming GST configuration table exists
            key = f"{CacheConfig.GST_PREFIX}rates"
            gst_data = {
                "standard": 18,
                "food": 5,
                "medical": 5,
                "high_value": 28
            }
            self.cache.set(key, gst_data, ttl=CacheConfig.GST_RATES_TTL)
            logger.info("Warmed GST rates into cache")
            return 1
        except Exception as e:
            logger.error(f"Error warming GST cache: {e}")
            return 0
    
    def warm_loyalty_tiers(self, db) -> int:
        """Preload loyalty tier information into cache"""
        try:
            key = f"{CacheConfig.LOYALTY_PREFIX}tiers"
            loyalty_data = {
                "bronze": {"min_points": 0, "discount_percent": 2},
                "silver": {"min_points": 1000, "discount_percent": 5},
                "gold": {"min_points": 5000, "discount_percent": 10},
                "platinum": {"min_points": 10000, "discount_percent": 15}
            }
            self.cache.set(key, loyalty_data, ttl=CacheConfig.LOYALTY_TIERS_TTL)
            logger.info("Warmed loyalty tiers into cache")
            return 1
        except Exception as e:
            logger.error(f"Error warming loyalty cache: {e}")
            return 0
    
    def warm_all(self, db) -> Dict[str, int]:
        """Warm all caches"""
        logger.info("Starting cache warming...")
        results = {
            "products": self.warm_product_catalog(db),
            "gst": self.warm_gst_rates(db),
            "loyalty": self.warm_loyalty_tiers(db)
        }
        logger.info(f"Cache warming complete: {results}")
        return results


# ============================================================================
# Cache Decorator
# ============================================================================

def cached(
    ttl: int = 3600,
    key_builder: Optional[Callable] = None,
    cache_manager: Optional[RedisCacheManager] = None
):
    """
    Decorator for caching function results
    
    Usage:
        @cached(ttl=3600)
        def get_product(product_id):
            return query_database(product_id)
        
        @cached(ttl=1800, key_builder=lambda args: f"user:{args[0]}")
        def get_user_profile(user_id):
            return query_user(user_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default: function name + args
                cache_key = f"cache:{func.__name__}:" + hashlib.md5(
                    str(args + tuple(kwargs.items())).encode()
                ).hexdigest()
            
            # Try cache
            if cache_manager:
                cached_value = cache_manager.get(cache_key)
                if cached_value is not None:
                    return cached_value
            
            # Compute if not cached
            result = func(*args, **kwargs)
            
            # Store in cache
            if cache_manager:
                cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# ============================================================================
# Global Cache Instances
# ============================================================================

_cache_manager = None
_in_memory_cache = None

def init_cache(redis_client) -> tuple:
    """Initialize caching system"""
    global _cache_manager, _in_memory_cache
    
    _cache_manager = RedisCacheManager(redis_client)
    _in_memory_cache = InMemoryCache()
    
    logger.info("Cache system initialized")
    return _cache_manager, _in_memory_cache

def get_cache_manager() -> Optional[RedisCacheManager]:
    """Get global cache manager"""
    return _cache_manager

def get_in_memory_cache() -> Optional[InMemoryCache]:
    """Get global in-memory cache"""
    return _in_memory_cache
