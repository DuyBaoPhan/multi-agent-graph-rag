"""
Neo4j Client — Module B1.1 (Async Version)
===========================================
Handles connection and Cypher queries for Graph RAG using Async driver.
"""

from neo4j import AsyncGraphDatabase
from loguru import logger
from src.config import get_settings

class Neo4jClient:
    def __init__(self):
        settings = get_settings()
        self.uri = settings.neo4j_uri
        self.user = settings.neo4j_user
        self.password = settings.neo4j_password
        self.driver = None

    async def connect(self):
        try:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
            await self.driver.verify_connectivity()
            await self._create_vector_indexes()
            logger.info("✅ Connected to Neo4j (Async) & Vector Indexes ready.")
        except Exception as e:
            logger.error(f"❌ Neo4j Connection Failed: {e}")
            self.driver = None

    async def _create_vector_indexes(self):
        """Create Vector Indexes for Semantic Search (Requirement B1.2)."""
        if not self.driver: return
        queries = [
            # Vector Index for MenuItems
            "CREATE VECTOR INDEX menu_embedding IF NOT EXISTS FOR (m:MenuItem) ON (m.embedding) "
            "OPTIONS {indexConfig: {`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}}",
            # Vector Index for Chunks
            "CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS FOR (c:Chunk) ON (c.embedding) "
            "OPTIONS {indexConfig: {`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}}"
        ]
        async with self.driver.session() as session:
            for q in queries:
                await session.run(q)

    async def close(self):
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed.")

    async def health_check(self) -> dict:
        try:
            if not self.driver: return {"status": "unhealthy", "error": "No driver"}
            await self.driver.verify_connectivity()
            return {"status": "healthy", "type": "neo4j"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    # --- Seeding Methods (Async) ---
    async def create_product(self, name, price, size, category, description, embedding=None):
        query = """
        MERGE (c:Entity {name: $category, type: 'Category'})
        MERGE (p:MenuItem {name: $name, size: $size})
        SET p.price = $price, p.description = $description, p.ingredients = 'Standard'
        SET p.embedding = $embedding
        MERGE (p)-[:BELONGS_TO]->(c)
        """
        if not self.driver:
            return
        async with self.driver.session() as session:
            await session.run(query, name=name, price=price, size=size, category=category, description=description, embedding=embedding)

    async def create_faq(self, question, answer, category, embedding=None):
        query = """
        MERGE (c:Entity {name: $category, type: 'Category'})
        MERGE (f:Chunk {content: $question, type: 'FAQ'})
        SET f.answer = $answer, f.embedding = $embedding
        MERGE (f)-[:MENTIONS]->(c)
        """
        if not self.driver:
            return
        async with self.driver.session() as session:
            await session.run(query, question=question, answer=answer, category=category, embedding=embedding)

    # --- RAG Queries (Async) ---
    async def graph_search_menu(self, query_text, top_k=5):
        cypher = """
        MATCH (p:MenuItem)
        WHERE p.name CONTAINS $query OR p.description CONTAINS $query
        WITH p LIMIT $top_k
        MATCH (p)-[:BELONGS_TO]->(c:Entity)<-[:BELONGS_TO]-(sibling:MenuItem)
        RETURN p, c.name as category, collect(sibling.name)[0..2] as related
        """
        if not self.driver:
            return []
        async with self.driver.session() as session:
            result = await session.run(cypher, query=query_text, top_k=top_k)
            records = await result.data()
            return records

    async def get_recommendations_by_category(self, category_name):
        cypher = """
        MATCH (c:Entity {name: $cat, type: 'Category'})<-[:BELONGS_TO]-(p:MenuItem)
        RETURN p.name as name, p.price as price, p.size as size
        ORDER BY p.price ASC
        """
        if not self.driver:
            return []
        async with self.driver.session() as session:
            result = await session.run(cypher, cat=category_name)
            records = await result.data()
            return records
    async def hybrid_search(self, vector, top_k=5):
        """Requirement B1.2: Hybrid Search with Graph Expansion (NEXT/MENTIONS)."""
        if not self.driver: return []
        
        # This query performs Vector Search + Graph Expansion in one hop
        cypher = """
        CALL db.index.vector.queryNodes('chunk_embedding', $top_k, $vector)
        YIELD node, score
        WHERE score >= 0.7
        OPTIONAL MATCH (node)-[:NEXT]->(next_chunk:Chunk)
        OPTIONAL MATCH (node)-[:MENTIONS]->(e:Entity)
        RETURN 
            node.content as content, 
            score, 
            collect(next_chunk.content) as expanded_context,
            collect(e.name) as entities
        """
        async with self.driver.session() as session:
            result = await session.run(cypher, vector=vector, top_k=top_k)
            return await result.data()

# Singleton instance
_client = None

def get_neo4j_client():
    global _client
    if _client is None:
        _client = Neo4jClient()
    return _client
