"""
Neo4j Graph Schema
====================
Schema definitions and initialization for the knowledge graph (Module B1.1).

Node Types:
  - MenuItem: Menu items with name, price, size, category
  - Chunk: Text chunks from documents with embeddings
  - Entity: Extracted entities (people, places, concepts)

Relationships:
  - NEXT/PREV: Sequential ordering of chunks
  - MENTIONS: Chunk mentions an Entity
  - BELONGS_TO: MenuItem belongs to a category
  - HAS_SIZE: MenuItem has size variants
"""

from loguru import logger

from src.graph_rag.neo4j_client import Neo4jClient

# Cypher statements for schema initialization
SCHEMA_CONSTRAINTS = [
    "CREATE CONSTRAINT menu_item_id IF NOT EXISTS FOR (m:MenuItem) REQUIRE m.id IS UNIQUE",
    "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
    "CREATE CONSTRAINT category_name IF NOT EXISTS FOR (cat:Category) REQUIRE cat.name IS UNIQUE",
]

SCHEMA_INDEXES = [
    "CREATE INDEX menu_item_name IF NOT EXISTS FOR (m:MenuItem) ON (m.name)",
    "CREATE INDEX menu_item_category IF NOT EXISTS FOR (m:MenuItem) ON (m.category)",
    "CREATE INDEX chunk_source IF NOT EXISTS FOR (c:Chunk) ON (c.source)",
]

# Vector indexes for hybrid search (Module B1.2)
VECTOR_INDEXES = [
    """CALL db.index.vector.createNodeIndex(
        'chunk_embedding',
        'Chunk',
        'embedding',
        1024,
        'cosine'
    )""",
    """CALL db.index.vector.createNodeIndex(
        'menu_embedding',
        'MenuItem',
        'embedding',
        1024,
        'cosine'
    )""",
]


async def initialize_schema(client: Neo4jClient):
    """Create all constraints, indexes, and vector indexes."""
    logger.info("Initializing Neo4j schema...")

    for constraint in SCHEMA_CONSTRAINTS:
        try:
            await client.run_query(constraint)
        except Exception as e:
            logger.debug(f"Constraint may already exist: {e}")

    for index in SCHEMA_INDEXES:
        try:
            await client.run_query(index)
        except Exception as e:
            logger.debug(f"Index may already exist: {e}")

    for vector_idx in VECTOR_INDEXES:
        try:
            await client.run_query(vector_idx)
        except Exception as e:
            logger.debug(f"Vector index may already exist: {e}")

    logger.info("✅ Neo4j schema initialized")
