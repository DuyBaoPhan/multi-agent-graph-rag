"""
Graph Expansion
=================
Traverse NEXT/PREV relationships to expand context (Module B1.2).
Increases recall by including neighboring chunks.
"""

from loguru import logger

from src.graph_rag.neo4j_client import Neo4jClient


async def expand_graph_context(
    client: Neo4jClient,
    chunk_ids: list[str],
    hops: int = 1,
) -> list[dict]:
    """
    Expand retrieved chunks by traversing NEXT/PREV relationships.
    
    Args:
        client: Neo4j client instance
        chunk_ids: IDs of initially retrieved chunks
        hops: Number of hops to traverse (1 = immediate neighbors)
        
    Returns:
        Expanded list of chunks including neighbors
    """
    if not chunk_ids:
        return []

    query = """
    UNWIND $chunk_ids AS cid
    MATCH (c:Chunk {id: cid})
    OPTIONAL MATCH (c)-[:NEXT*1..$hops]->(next:Chunk)
    OPTIONAL MATCH (c)<-[:NEXT*1..$hops]-(prev:Chunk)
    WITH collect(DISTINCT c) + collect(DISTINCT next) + collect(DISTINCT prev) AS all_chunks
    UNWIND all_chunks AS chunk
    WHERE chunk IS NOT NULL
    RETURN DISTINCT chunk.id AS id, chunk.text AS text, chunk.source AS source,
           chunk.position AS position
    ORDER BY chunk.source, chunk.position
    """
    results = await client.run_query(
        query, {"chunk_ids": chunk_ids, "hops": hops}
    )
    logger.debug(f"Graph expansion: {len(chunk_ids)} → {len(results)} chunks")
    return results
