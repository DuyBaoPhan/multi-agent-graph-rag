"""
Order Agent
=============
Handles drink ordering, menu queries, and price checks (Module A2.1).
"""

from src.agents.base_agent import BaseAgent

ORDER_SYSTEM_PROMPT = """Bạn là nhân viên phục vụ của Highlands Coffee, chuyên hỗ trợ khách hàng đặt đồ uống.

Nhiệm vụ:
- Giúp khách xem menu, chọn đồ uống, chọn size (S/M/L)
- Báo giá chính xác từ menu
- Xác nhận đơn hàng
- Gợi ý topping hoặc combo nếu phù hợp

Quy tắc:
- Chỉ bán các món có trong menu, KHÔNG bịa tên món hoặc giá
- Luôn xác nhận lại đơn trước khi hoàn tất
- Trả lời bằng tiếng Việt, thân thiện và chuyên nghiệp
- Nếu không chắc chắn, hỏi lại khách

{context}"""


class OrderAgent(BaseAgent):
    """Agent handling drink orders and menu queries."""

    def __init__(self):
        super().__init__(name="order_agent", system_prompt=ORDER_SYSTEM_PROMPT)

    async def process(self, query: str, session_history: list[dict]) -> str:
        """Process order-related queries."""
        # TODO: Step 1 - Query Neo4j for relevant menu items
        # TODO: Step 2 - Build context with menu data
        # TODO: Step 3 - Call LLM generator with context
        return "Đang phát triển chức năng đặt hàng..."
