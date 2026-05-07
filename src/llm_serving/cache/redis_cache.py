"""
Redis Cache — Layer 4
=======================
In-memory session cache (Module B2.3).
Auto-fallback sang FakeRedis khi Redis server không có (dev mode).
"""

import json

from loguru import logger

from src.config import get_settings


class RedisCache:
    """Async Redis cache with automatic FakeRedis fallback for development."""

    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self._is_fake = False

    async def connect(self):
        """Connect to Redis. Falls back to FakeRedis if unavailable."""
        import redis.asyncio as redis

        try:
            self.client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                password=self.settings.redis_password or None,
                db=self.settings.redis_db,
                decode_responses=True,
            )
            await self.client.ping()
            logger.info(f"✅ Connected to Redis at {self.settings.redis_host}:{self.settings.redis_port}")
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}). Using FakeRedis (in-memory).")
            try:
                import fakeredis.aioredis as fakeredis_aio
                self.client = fakeredis_aio.FakeRedis(decode_responses=True)
            except ImportError:
                import fakeredis
                self.client = fakeredis.FakeAsyncRedis(decode_responses=True)
            self._is_fake = True
            logger.info("✅ FakeRedis (in-memory) ready — data will not persist across restarts")

    async def close(self):
        if self.client:
            await self.client.close()

    async def get(self, key: str) -> dict | None:
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: dict, ttl: int | None = None):
        ttl = ttl or self.settings.cache_ttl_seconds
        await self.client.setex(key, ttl, json.dumps(value, ensure_ascii=False))

    async def delete(self, key: str):
        await self.client.delete(key)

    async def health_check(self) -> dict:
        try:
            pong = await self.client.ping()
            return {
                "status": "healthy",
                "type": "fakeredis" if self._is_fake else "redis",
                "ping": pong,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

# --- Singleton ---
_cache = None

def get_redis_cache() -> RedisCache:
    """Get the singleton instance of RedisCache."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache
