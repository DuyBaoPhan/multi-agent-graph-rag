"""
FAQ Agent — Module A2.1 (Upgraded)
====================================
Answers FAQs using a Hybrid RAG Pipeline:
1. Dual-Domain Search (Keyword + Vector)
2. Lite Graph Expansion (Category-based)
3. Late Reranking
"""

from loguru import logger
from src.agents.base_agent import BaseAgent
from src.graph_rag.knowledge_store import get_knowledge_store
from src.graph_rag.neo4j_client import get_neo4j_client

FAQ_SYSTEM_PROMPT = """Bạn là trợ lý thông tin của Highlands Coffee. 
Nhiệm vụ: Giải đáp thắc mắc của khách hàng về chính sách, wifi, giờ mở cửa, v.v.
Quy tắc:
1. Chỉ trả lời dựa trên thông tin chính thức được cung cấp.
2. Nếu không biết, hãy hướng dẫn khách liên hệ hotline 1900-xxxx.
3. Trả lời lịch sự, ngắn gọn và hữu ích."""


class FAQAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="faq_agent", system_prompt=FAQ_SYSTEM_PROMPT)

    async def process(
        self, query: str, session_history: list[dict], session_id: str | None = None
    ) -> str:
        store = get_knowledge_store()
        neo4j = get_neo4j_client()
        
        # 1. Try Graph Search for FAQ (Safety check for driver)
        results = []
        try:
            if neo4j.driver:
                cypher = """
                MATCH (f:Chunk) 
                WHERE f.type = 'FAQ' AND (f.content CONTAINS $q OR f.answer CONTAINS $q) 
                RETURN f.content as question, f.answer as answer LIMIT 3
                """
                async with neo4j.driver.session() as session:
                    res = await session.run(cypher, q=query)
                    results = await res.data()
            else:
                logger.warning("Neo4j driver is None, skipping graph search.")
        except Exception as e:
            logger.warning(f"Neo4j FAQ search failed: {e}")
            results = []

        # 2. Fallback to local KnowledgeStore if graph search yield no results
        if not results:
            local_results = store.search_faq(query, top_k=3)
            # Standardize format for the rest of the function
            results = [{"question": r.question, "answer": r.answer} for r in local_results]

        if not results:
            return "Dạ, hiện tại Highlands chưa có thông tin cụ thể về vấn đề này ạ. Anh/Chị vui lòng liên hệ hotline 1900-xxxx để em hỗ trợ mình nhanh nhất nhé!"

        # 3. Build response using the standardized results list
        
        # 2. Build response
        main_answer = results[0]['answer']
        
        if len(results) > 1:
            related = "\n\n💡 Thông tin liên quan:\n"
            for r in results[1:]:
                related += f"- {r['question']}\n"
            return f"{main_answer}{related}"
        
        return main_answer
