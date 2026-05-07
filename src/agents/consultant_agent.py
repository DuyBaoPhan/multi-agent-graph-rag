"""
Consultant Agent
==================
Provides drink recommendations combining menu + FAQ knowledge (Module A2.1).
"""

from src.agents.base_agent import BaseAgent

CONSULTANT_SYSTEM_PROMPT = """Bạn là chuyên gia tư vấn đồ uống của Highlands Coffee.

Nhiệm vụ:
- Tư vấn đồ uống phù hợp theo sở thích, thời tiết, dịp đặc biệt
- So sánh các loại đồ uống khi khách phân vân
- Gợi ý combo, topping, size phù hợp
- Chia sẻ thông tin về nguyên liệu, cách pha chế

Quy tắc:
- Dựa trên menu thực tế để tư vấn
- Cá nhân hóa gợi ý theo context cuộc hội thoại
- Nhiệt tình, am hiểu, tạo trải nghiệm tốt cho khách
- Trả lời bằng tiếng Việt, tự nhiên như barista thực thụ

Menu & Context:
{context}"""


class ConsultantAgent(BaseAgent):
    """Agent providing personalized drink recommendations."""

    def __init__(self):
        super().__init__(name="consultant_agent", system_prompt=CONSULTANT_SYSTEM_PROMPT)

    async def process(self, query: str, session_history: list[dict]) -> str:
        """Process consultation queries combining menu and FAQ data."""
        # TODO: Step 1 - Query both menu items and FAQ from Neo4j
        # TODO: Step 2 - Build rich context with both data sources
        # TODO: Step 3 - Call LLM generator with personalized context
        return "Đang phát triển chức năng tư vấn..."
