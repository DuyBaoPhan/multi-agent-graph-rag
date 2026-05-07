"""
Reranker
==========
Late reranking with BGE Reranker for improved precision (Module B1.2).
"""

import httpx
from loguru import logger


async def rerank(
    query: str,
    documents: list[dict],
    top_k: int = 5,
    reranker_url: str = "http://localhost:8081",
) -> list[dict]:
    """
    Rerank documents using BGE Reranker model.
    
    Args:
        query: Original user query
        documents: List of candidate documents with 'text' field
        top_k: Number of top documents to return after reranking
        reranker_url: URL of the reranker service
        
    Returns:
        Top-k reranked documents
    """
    if not documents:
        return []

    pairs = [{"text": query, "text_pair": doc["text"]} for doc in documents]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{reranker_url}/rerank",
                json={"query": query, "texts": [doc["text"] for doc in documents]},
            )
            response.raise_for_status()
            scores = response.json()

        # Attach scores and sort
        for i, doc in enumerate(documents):
            doc["rerank_score"] = scores[i] if i < len(scores) else 0.0

        reranked = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]

    except Exception as e:
        logger.warning(f"Reranking failed, returning original order: {e}")
        return documents[:top_k]
