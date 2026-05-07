"""
FAQ Agent
===========
Handles frequently asked questions using Hybrid RAG (Module A2.1).
"""

from src.agents.base_agent import BaseAgent

FAQ_SYSTEM_PROMPT = """Bạn là trợ lý thông tin của Highlands Coffee, chuyên trả lời các câu hỏi thường gặp.

Nhiệm vụ:
- Trả lời về giờ mở cửa, địa chỉ, chính sách
- Giải đáp về chương trình khuyến mãi, thẻ thành viên
- Cung cấp thông tin về thương hiệu Highlands Coffee

Quy tắc:
- CHỈ trả lời dựa trên thông tin được cung cấp trong context
- Nếu không có thông tin, nói rõ "Tôi chưa có thông tin này"
- KHÔNG bịa thông tin
- Trả lời ngắn gọn, rõ ràng bằng tiếng Việt

Context:
{context}"""


class FAQAgent(BaseAgent):
    """Agent handling FAQ queries with Hybrid RAG pipeline."""

    def __init__(self):
        super().__init__(name="faq_agent", system_prompt=FAQ_SYSTEM_PROMPT)

    async def process(self, query: str, session_history: list[dict]) -> str:
        """Process FAQ queries using Graph RAG pipeline."""
        # TODO: Step 1 - Run Hybrid Search (vector + keyword)
        # TODO: Step 2 - Graph Expansion (NEXT/PREV nodes)
        # TODO: Step 3 - Rerank with BGE Reranker
        # TODO: Step 4 - Build context from top-k chunks
        # TODO: Step 5 - Call LLM generator
        return "Đang phát triển chức năng FAQ..."
