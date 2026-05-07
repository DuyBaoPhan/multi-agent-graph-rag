import asyncio
import sys
import io

# Set encoding for Windows terminal
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.agents.faq_agent import FAQAgent
from src.agents.consultant_agent import ConsultantAgent
from src.graph_rag.knowledge_store import get_knowledge_store

async def test():
    store = get_knowledge_store()
    store.load_from_csv()
    
    faq = FAQAgent()
    con = ConsultantAgent()
    
    print("--- FAQ Test: WiFi ---")
    print(await faq.process("wifi password là gì", []))
    
    print("\n--- Consultant Test: Nóng ---")
    print(await con.process("món gì mát cho ngày nóng", []))
    
    print("\n--- Consultant Test: Rẻ ---")
    print(await con.process("có món nào dưới 30k không", []))

if __name__ == "__main__":
    asyncio.run(test())
