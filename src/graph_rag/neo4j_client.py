"""
Neo4j Client
===============
Async Neo4j driver wrapper for graph operations (Module B1.1).
"""

from contextlib import asynccontextmanager

from neo4j import AsyncGraphDatabase
from loguru import logger

from src.config import get_settings


class Neo4jClient:
    """
    Async Neo4j client for graph database operations.
    
    Handles connection pooling, query execution, and schema management.
    """

    def __init__(self):
        self.settings = get_settings()
        self.driver = None

    async def connect(self):
        """Initialize the Neo4j async driver."""
        self.driver = AsyncGraphDatabase.driver(
            self.settings.neo4j_uri,
            auth=(self.settings.neo4j_user, self.settings.neo4j_password),
        )
        # Verify connectivity
        await self.driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {self.settings.neo4j_uri}")

    async def close(self):
        """Close the Neo4j driver."""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")

    @asynccontextmanager
    async def session(self):
        """Get an async Neo4j session."""
        async with self.driver.session(
            database=self.settings.neo4j_database
        ) as session:
            yield session

    async def run_query(self, query: str, params: dict | None = None) -> list[dict]:
        """Execute a Cypher query and return results as list of dicts."""
        async with self.session() as session:
            result = await session.run(query, params or {})
            records = [record.data() async for record in result]
            return records

    async def health_check(self) -> bool:
        """Check if Neo4j is reachable."""
        try:
            await self.driver.verify_connectivity()
            return True
        except Exception:
            return False
