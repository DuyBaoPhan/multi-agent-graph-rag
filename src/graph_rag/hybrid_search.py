"""
Hybrid Search
===============
Dual-domain search combining vector + keyword search (Module B1.2).
"""

from loguru import logger

from src.graph_rag.neo4j_client import Neo4jClient


async def hybrid_search(
    client: Neo4jClient,
    query_embedding: list[float],
    query_text: str,
    top_k: int = 10,
    vector_weight: float = 0.7,
) -> list[dict]:
    """
    Perform hybrid search: vector similarity + keyword matching.
    
    Args:
        client: Neo4j client instance
        query_embedding: Query embedding vector from TEI
        query_text: Original query text for keyword search
        top_k: Number of results to return
        vector_weight: Weight for vector vs keyword score (0-1)
        
    Returns:
        List of matched chunks with scores
    """
    # Step 1: Vector search
    vector_results = await _vector_search(client, query_embedding, top_k * 2)

    # Step 2: Keyword search (fulltext)
    keyword_results = await _keyword_search(client, query_text, top_k * 2)

    # Step 3: Merge and score
    merged = _merge_results(vector_results, keyword_results, vector_weight)

    return sorted(merged, key=lambda x: x["score"], reverse=True)[:top_k]


async def _vector_search(
    client: Neo4jClient, embedding: list[float], top_k: int
) -> list[dict]:
    """Search using vector similarity index."""
    query = """
    CALL db.index.vector.queryNodes('chunk_embedding', $top_k, $embedding)
    YIELD node, score
    RETURN node.id AS id, node.text AS text, node.source AS source, score
    """
    return await client.run_query(query, {"embedding": embedding, "top_k": top_k})


async def _keyword_search(
    client: Neo4jClient, text: str, top_k: int
) -> list[dict]:
    """Search using fulltext keyword index."""
    # TODO: Create fulltext index and implement keyword search
    return []


def _merge_results(
    vector_results: list[dict],
    keyword_results: list[dict],
    vector_weight: float,
) -> list[dict]:
    """Merge vector and keyword results with weighted scoring."""
    merged: dict[str, dict] = {}

    for r in vector_results:
        rid = r["id"]
        merged[rid] = {**r, "score": r.get("score", 0) * vector_weight}

    keyword_weight = 1.0 - vector_weight
    for r in keyword_results:
        rid = r["id"]
        if rid in merged:
            merged[rid]["score"] += r.get("score", 0) * keyword_weight
        else:
            merged[rid] = {**r, "score": r.get("score", 0) * keyword_weight}

    return list(merged.values())
