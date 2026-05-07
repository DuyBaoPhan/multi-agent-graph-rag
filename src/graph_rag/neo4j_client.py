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
            logger.info("✅ Connected to Neo4j (Async) successfully.")
        except Exception as e:
            logger.error(f"❌ Neo4j Connection Failed: {e}")
            self.driver = None

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
    async def create_product(self, name, price, size, category, description):
        query = """
        MERGE (c:Category {name: $category})
        MERGE (p:Product {name: $name, size: $size})
        SET p.price = $price, p.description = $description
        MERGE (p)-[:BELONGS_TO]->(c)
        """
        async with self.driver.session() as session:
            await session.run(query, name=name, price=price, size=size, category=category, description=description)

    async def create_faq(self, question, answer, category):
        query = """
        MERGE (c:Category {name: $category})
        MERGE (f:FAQ {question: $question})
        SET f.answer = $answer
        MERGE (f)-[:RELEVANT_TO]->(c)
        """
        async with self.driver.session() as session:
            await session.run(query, question=question, answer=answer, category=category)

    # --- RAG Queries (Async) ---
    async def graph_search_menu(self, query_text, top_k=5):
        cypher = """
        MATCH (p:Product)
        WHERE p.name CONTAINS $query OR p.description CONTAINS $query
        WITH p LIMIT $top_k
        MATCH (p)-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(sibling:Product)
        RETURN p, c.name as category, collect(sibling.name)[0..2] as related
        """
        async with self.driver.session() as session:
            result = await session.run(cypher, query=query_text, top_k=top_k)
            records = await result.data()
            return records

    async def get_recommendations_by_category(self, category_name):
        cypher = """
        MATCH (c:Category {name: $cat})<-[:BELONGS_TO]-(p:Product)
        RETURN p.name as name, p.price as price, p.size as size
        ORDER BY p.price ASC
        """
        async with self.driver.session() as session:
            result = await session.run(cypher, cat=category_name)
            records = await result.data()
            return records

# Singleton instance
_client = None

def get_neo4j_client():
    global _client
    if _client is None:
        _client = Neo4jClient()
    return _client
