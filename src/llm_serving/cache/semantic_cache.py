"""
Semantic Cache
================
Embedding-based semantic cache for similar queries (Module B2.3, C2.2).
Uses cosine similarity ≥ threshold to detect cache hits.
"""

import numpy as np
from loguru import logger

from src.config import get_settings


class SemanticCache:
    """
    Cache that matches queries by semantic similarity rather than exact match.
    
    Stores query embeddings and responses, returning cached response
    when a new query is semantically similar (cosine sim ≥ threshold).
    """

    def __init__(self):
        self.settings = get_settings()
        self.threshold = self.settings.semantic_cache_threshold
        # In-memory store: list of (embedding, response) tuples
        # TODO: Replace with Qdrant/Redis vector store for production
        self.cache: list[tuple[np.ndarray, dict]] = []

    def lookup(self, query_embedding: list[float]) -> dict | None:
        """
        Look up a similar query in the cache.
        
        Args:
            query_embedding: Embedding of the new query
            
        Returns:
            Cached response dict if hit, None if miss
        """
        if not self.cache:
            return None

        query_vec = np.array(query_embedding)

        best_score = 0.0
        best_response = None

        for cached_embedding, response in self.cache:
            score = self._cosine_similarity(query_vec, cached_embedding)
            if score > best_score:
                best_score = score
                best_response = response

        if best_score >= self.threshold:
            logger.info(f"Semantic cache HIT (similarity={best_score:.4f})")
            return best_response

        logger.debug(f"Semantic cache MISS (best similarity={best_score:.4f})")
        return None

    def store(self, query_embedding: list[float], response: dict):
        """Store a query-response pair in the cache."""
        vec = np.array(query_embedding)
        self.cache.append((vec, response))

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot = np.dot(a, b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm == 0:
            return 0.0
        return float(dot / norm)
