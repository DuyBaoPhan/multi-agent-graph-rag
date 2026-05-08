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
        self._local_index = [] # List of (embedding, query, response)

    async def get(self, query: str, intent: str = None) -> str | None:
        """Retrieve from semantic cache, but SKIP if it's a dynamic intent like 'order'."""
        # STRATEGIC FIX: Never cache or retrieve orders/billing data
        billing_keywords = ["bill", "tổng", "tiền", "hóa đơn", "thanh toán", "giỏ hàng", "đã đặt"]
        query_lower = query.lower()
        
        if intent in ["order", "billing", "payment"] or any(k in query_lower for k in billing_keywords):
            return None
        
        try:
            # 1. Check exact match in Redis first (Fast path)
            exact = await self.redis.get(f"scache:exact:{query}")
            if exact: return exact["reply"]

            # 2. Semantic Search (Simplified for demo: using local list)
            # In a full prod system, we'd use RediSearch Vector Similarity
            query_emb = self.store._embedder.encode(query)
            
            import numpy as np
            best_score = 0
            best_reply = None

            for emb, q, reply in self._local_index:
                score = np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb))
                if score > best_score:
                    best_score = score
                    best_reply = reply
            
            if best_score >= self.threshold:
                logger.info(f"🚀 Semantic Cache Hit ({best_score:.2f}) for: {query}")
                return best_reply
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        
        return None

    async def set(self, query: str, response: str, intent: str = None):
        """Store query and response if it's a stable intent (FAQ/Ignore)."""
        billing_keywords = ["bill", "tổng", "tiền", "hóa đơn", "thanh toán", "giỏ hàng", "đã đặt"]
        query_lower = query.lower()
        if intent in ["order", "billing", "payment"] or any(kw in query_lower for kw in billing_keywords):
            return
        
        try:
            # Store exact
            await self.redis.set(f"scache:exact:{query}", {"reply": response}, ttl=3600)
            
            # Store for semantic search
            if self.store._embedder:
                emb = self.store._embedder.encode(query)
                self._local_index.append((emb, query, response))
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

# Singleton
_cache = None

def get_semantic_cache() -> SemanticCache:
    global _cache
    if _cache is None:
        _cache = SemanticCache()
    return _cache
