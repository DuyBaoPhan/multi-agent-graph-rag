import asyncio
import sys
import io

# Set encoding for Windows terminal
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.router.serving import classify_intent
from src.agents.order_agent import OrderAgent
from src.graph_rag.knowledge_store import get_knowledge_store

async def test():
    get_knowledge_store().load_from_csv()
    
    print("--- Test 1: Intent Check ---")
    intent_res = await classify_intent("bán có bán cafe không")
    print(f"Query: 'bán có bán cafe không' -> Action: {intent_res['action']}")
    
    print("\n--- Test 2: Size Check ---")
    agent = OrderAgent()
    order_res = await agent.process("bán cho tôi 3 ly cafe sữa đá size L", [], "sid_123")
    print(order_res)

if __name__ == "__main__":
    asyncio.run(test())
