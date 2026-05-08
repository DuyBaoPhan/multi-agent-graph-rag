import asyncio
from src.graph_rag.neo4j_client import get_neo4j_client

async def main():
    neo4j = get_neo4j_client()
    try:
        res = await neo4j.graph_search_menu("Bánh Mì Que Gà Cay", top_k=5)
        print("Neo4j results:")
        for r in res:
            print(r['p']['name'], r['p']['price'])
    except Exception as e:
        print("Neo4j error:", e)

asyncio.run(main())
