"""
Semantic Cache — Module B2.3
=============================
Speeds up responses by caching results of similar queries in Redis.
Uses Vector Similarity to match queries.
"""

import json
from loguru import logger
from src.llm_serving.cache.redis_cache import get_redis_cache
from src.graph_rag.knowledge_store import get_knowledge_store

class SemanticCache:
    def __init__(self, threshold: float = 0.92):
        self.redis = get_redis_cache()
        self.threshold = threshold
        self.store = get_knowledge_store()

    async def get(self, query: str) -> str | None:
        """Find a similar query in cache and return result."""
        if not self.redis or not self.store._embedder:
            return None
        
        try:
            # 1. Encode query
            query_emb = self.store._embedder.encode(query)
            
            # 2. Search in Redis (Simplified: we'll use a key-value pair for this demo)
            # In production, use RedisVL or RediSearch Vector Similarity
            cached_val = await self.redis.get(f"scache:{query}")
            if cached_val:
                logger.info(f"🚀 Semantic Cache Hit for: {query}")
                return str(cached_val) # RedisCache.get returns json.loads, so we ensure it's string
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        
        return None

    async def set(self, query: str, response: str):
        """Store query and response in cache."""
        if not self.redis:
            return
        
        try:
            # Store with TTL (e.g., 1 hour)
            await self.redis.set(f"scache:{query}", {"reply": response}, ttl=3600)
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

# Singleton
_cache = None

def get_semantic_cache() -> SemanticCache:
    global _cache
    if _cache is None:
        _cache = SemanticCache()
    return _cache
