"""
Neo4j Seed Script
===================
Seed Neo4j with initial Highlands Coffee menu data (Module B1.1).
"""

import asyncio

from loguru import logger

# Sample Highlands Coffee menu data (≥100 items needed)
SAMPLE_MENU = [
    {"name": "Phin Sữa Đá", "price": 29000, "sizes": {"S": 29000, "M": 35000, "L": 39000}, "category": "Cà Phê"},
    {"name": "Phin Đen Đá", "price": 29000, "sizes": {"S": 29000, "M": 35000, "L": 39000}, "category": "Cà Phê"},
    {"name": "Bạc Xỉu", "price": 29000, "sizes": {"S": 29000, "M": 35000, "L": 39000}, "category": "Cà Phê"},
    {"name": "Cà Phê Sữa Đá", "price": 29000, "sizes": {"S": 29000, "M": 35000, "L": 39000}, "category": "Cà Phê"},
    {"name": "Phindi Hạnh Nhân", "price": 45000, "sizes": {"M": 45000, "L": 49000}, "category": "Phindi"},
    {"name": "Phindi Choco", "price": 45000, "sizes": {"M": 45000, "L": 49000}, "category": "Phindi"},
    {"name": "Phindi Kem Sữa", "price": 45000, "sizes": {"M": 45000, "L": 49000}, "category": "Phindi"},
    {"name": "Freeze Trà Xanh", "price": 55000, "sizes": {"M": 55000, "L": 65000}, "category": "Freeze"},
    {"name": "Freeze Cookies & Cream", "price": 55000, "sizes": {"M": 55000, "L": 65000}, "category": "Freeze"},
    {"name": "Freeze Sô-cô-la", "price": 55000, "sizes": {"M": 55000, "L": 65000}, "category": "Freeze"},
    {"name": "Trà Sen Vàng", "price": 45000, "sizes": {"M": 45000, "L": 55000}, "category": "Trà"},
    {"name": "Trà Thạch Đào", "price": 45000, "sizes": {"M": 45000, "L": 55000}, "category": "Trà"},
    {"name": "Trà Thanh Đào", "price": 45000, "sizes": {"M": 45000, "L": 55000}, "category": "Trà"},
    # TODO: Add remaining items to reach ≥ 100
]


async def seed_menu(neo4j_client):
    """Seed Neo4j with menu items."""
    logger.info(f"Seeding {len(SAMPLE_MENU)} menu items...")

    for item in SAMPLE_MENU:
        query = """
        MERGE (m:MenuItem {name: $name})
        SET m.category = $category, m.base_price = $base_price
        WITH m
        MERGE (cat:Category {name: $category})
        MERGE (m)-[:BELONGS_TO]->(cat)
        """
        await neo4j_client.run_query(query, {
            "name": item["name"],
            "category": item["category"],
            "base_price": item["price"],
        })

        # Create size variants
        for size, price in item.get("sizes", {}).items():
            size_query = """
            MATCH (m:MenuItem {name: $name})
            MERGE (s:Size {name: $size, price: $price})
            MERGE (m)-[:HAS_SIZE]->(s)
            """
            await neo4j_client.run_query(size_query, {
                "name": item["name"],
                "size": size,
                "price": price,
            })

    logger.info("✅ Menu seeding complete")


if __name__ == "__main__":
    asyncio.run(seed_menu(None))  # Pass actual client
