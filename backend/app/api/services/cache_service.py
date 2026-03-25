"""
Redis Cache Service for Dashboard Metrics
Prevents 424K-record scans on every dashboard refresh
Per CLAUDE.md Part 3.3
"""
import redis
import json
import os
from functools import wraps
from dotenv import load_dotenv

load_dotenv('backend/.env')

r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

def cache(key_prefix: str, ttl_seconds: int = 60):
    """
    Cache decorator for expensive database queries
    Usage:
        @cache("dashboard_metrics", ttl_seconds=60)
        async def get_dashboard_metrics(tenant_id: int, db):
            # This query runs once per minute, not 50x per day
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"
            cached = r.get(cache_key)
            if cached:
                return json.loads(cached)
            result = await func(*args, **kwargs)
            r.setex(cache_key, ttl_seconds, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator
