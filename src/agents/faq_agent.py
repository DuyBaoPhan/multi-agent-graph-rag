"""
FAQ Agent — Module A2.1 (Upgraded)
====================================
Answers FAQs using a Hybrid RAG Pipeline:
1. Dual-Domain Search (Keyword + Vector)
2. Lite Graph Expansion (Category-based)
3. Late Reranking
"""

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
        
        # 1. Try Graph Search for FAQ
        try:
            # We use a simple Cypher to find matching FAQ questions
            cypher = "MATCH (f:FAQ) WHERE f.question CONTAINS $q OR f.answer CONTAINS $q RETURN f LIMIT 3"
            async with neo4j.driver.session() as session:
                res = await session.run(cypher, q=query)
                records = await res.data()
                results = [r['f'] for r in records]
        except Exception as e:
            logger.warning(f"Neo4j FAQ search failed: {e}")
            results = store.search_faq(query, top_k=3)

        if not results:
            return "Xin lỗi, hiện tại tôi chưa có thông tin cụ thể về vấn đề này. Bạn vui lòng liên hệ hotline 1900-xxxx hoặc inbox fanpage Highlands Coffee để được hỗ trợ nhanh nhất nhé!"

        # 2. Graph Expansion (Optional for FAQ, could show related questions)
        # For FAQ, we just take the best match but show related info
        faq_text = store.format_faq_entries(results)
        
        # Build response
        main_answer = results[0].answer
        
        # If there are more results, add them as "related info"
        if len(results) > 1:
            related = "\n\n💡 Thông tin liên quan:\n"
            for r in results[1:]:
                related += f"- {r.question}\n"
            return f"{main_answer}{related}"
        
        return main_answer
