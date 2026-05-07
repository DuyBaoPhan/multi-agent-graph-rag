import asyncio
import sys
import io

# Set encoding for Windows terminal
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from src.agents.order_agent import OrderAgent
from src.agents.session_store import get_session_store
from src.graph_rag.knowledge_store import get_knowledge_store

async def test():
    # Load data
    get_knowledge_store().load_from_csv()
    
    agent = OrderAgent()
    sid = "test_session_123"
    
    print("--- Test 1: Add item ---")
    res1 = await agent.process("cho mình 2 bạc xỉu", [], sid)
    print(res1)
    
    print("\n--- Test 2: Add another item ---")
    res2 = await agent.process("thêm 1 phin sữa đá", [], sid)
    print(res2)
    
    print("\n--- Test 3: View cart ---")
    res3 = await agent.process("xem giỏ hàng", [], sid)
    print(res3)
    
    print("\n--- Test 4: Remove item ---")
    res4 = await agent.process("xóa bạc xỉu", [], sid)
    print(res4)
    
    print("\n--- Test 5: Checkout ---")
    res5 = await agent.process("tính tiền", [], sid)
    print(res5)

if __name__ == "__main__":
    asyncio.run(test())
