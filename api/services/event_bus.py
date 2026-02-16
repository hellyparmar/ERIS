"""
Event Bus using Redis Streams
Connects all modules together per CLAUDE.md Part 1.3
"""
import redis
import json
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

def publish_event(stream: str, data: dict):
    """Publish event to Redis stream"""
    r.xadd(stream, {'payload': json.dumps(data)})

def subscribe_events(stream: str, group: str, consumer: str):
    """Subscribe to Redis stream events"""
    try:
        r.xgroup_create(stream, group, id='0', mkstream=True)
    except Exception:
        pass  # group already exists
    return r.xreadgroup(group, consumer, {stream: '>'}, count=10, block=1000)
