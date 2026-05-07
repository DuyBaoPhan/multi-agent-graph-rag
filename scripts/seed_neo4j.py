"""
Neo4j Seeding Script — Module B1.2
===================================
Loads Menu and FAQ data from CSV into Neo4j Graph.
"""

import csv
import asyncio
from pathlib import Path
from loguru import logger
from src.graph_rag.neo4j_client import get_neo4j_client

MENU_CSV = "data/raw/menu/highlands_menu.csv"
FAQ_CSV = "data/raw/faq/highlands_faq.csv"

async def seed_database():
    client = get_neo4j_client()
    await client.connect()
    if not client.driver:
        logger.error("Could not connect to Neo4j. Is the server running?")
        return

    # 1. Clear existing data
    logger.info("Cleaning up old data in Neo4j...")
    async with client.driver.session() as session:
        await session.run("MATCH (n) DETACH DELETE n")

    # 2. Seed Menu Items
    logger.info(f"Seeding Menu from {MENU_CSV}...")
    with open(MENU_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            await client.create_product(
                name=row["name"],
                price=int(row["price"]),
                size=row["size"],
                category=row["category"],
                description=row["description"]
            )
            count += 1
        logger.info(f"✅ Created {count} Product nodes.")

    # 3. Seed FAQ Entries
    logger.info(f"Seeding FAQ from {FAQ_CSV}...")
    with open(FAQ_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            await client.create_faq(
                question=row["question"],
                answer=row["answer"],
                category=row["category"]
            )
            count += 1
        logger.info(f"✅ Created {count} FAQ nodes.")

    await client.close()
    logger.info("🎉 Database seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_database())
