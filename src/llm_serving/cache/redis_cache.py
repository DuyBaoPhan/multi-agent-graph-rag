"""
Redis Cache
=============
Layer 4: In-memory session cache using Redis (Module B2.3).
"""

import json

import redis.asyncio as redis
from loguru import logger

from src.config import get_settings


class RedisCache:
    """Async Redis cache for session data and query results."""

    def __init__(self):
        self.settings = get_settings()
        self.client: redis.Redis | None = None

    async def connect(self):
        """Initialize Redis connection."""
        self.client = redis.Redis(
            host=self.settings.redis_host,
            port=self.settings.redis_port,
            password=self.settings.redis_password or None,
            db=self.settings.redis_db,
            decode_responses=True,
        )
        await self.client.ping()
        logger.info(f"Connected to Redis at {self.settings.redis_host}:{self.settings.redis_port}")

    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()

    async def get(self, key: str) -> dict | None:
        """Get a cached value by key."""
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: dict, ttl: int | None = None):
        """Set a cached value with optional TTL."""
        ttl = ttl or self.settings.cache_ttl_seconds
        await self.client.setex(key, ttl, json.dumps(value, ensure_ascii=False))

    async def delete(self, key: str):
        """Delete a cached key."""
        await self.client.delete(key)

    async def health_check(self) -> bool:
        """Check if Redis is reachable."""
        try:
            return await self.client.ping()
        except Exception:
            return False
