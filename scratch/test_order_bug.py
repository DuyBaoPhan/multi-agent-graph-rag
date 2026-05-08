import asyncio
from src.agents.order_agent import OrderAgent
from src.agents.session_store import get_session_store
from src.graph_rag.knowledge_store import get_knowledge_store
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def main():
    get_knowledge_store().load_from_csv()
    agent = OrderAgent()
    sid = "bug_session_02"
    
    res1 = await agent.process("Cho tôi order 1 ly latte M và 2 Cappuccino size L", [], sid)
    print("Turn 1:", res1)
    
    # Check cart
    store = get_session_store()
    meta = await store.get_metadata_async(sid)
    print("Cart 1:", meta.get("cart"))
    
    # Send second request with history
    history = [
        {"role": "user", "content": "Cho tôi order 1 ly latte M và 2 Cappuccino size L"},
        {"role": "assistant", "content": res1}
    ]
    res2 = await agent.process("thêm 1 cái bánh mì que gà cay", history, sid)
    print("Turn 2:", res2)
    
    meta2 = await store.get_metadata_async(sid)
    print("Cart 2:", meta2.get("cart"))

asyncio.run(main())
