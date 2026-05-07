"""
Consultant Agent — Module A2.1 (Upgraded)
========================================
Personalized drink recommendations using Context-aware Hybrid RAG.
Considers: Taste, Budget, Weather, and Health.
"""

import random
from src.agents.base_agent import BaseAgent
from src.graph_rag.knowledge_store import get_knowledge_store
from src.graph_rag.neo4j_client import get_neo4j_client

CONSULTANT_SYSTEM_PROMPT = """Bạn là chuyên gia tư vấn đồ uống (Drink Consultant) tại Highlands Coffee.
Nhiệm vụ: Gợi ý món phù hợp nhất dựa trên sở thích, ngân sách và điều kiện thời tiết.
Quy tắc:
1. Luôn hỏi thêm về sở thích nếu thông tin chưa rõ.
2. Gợi ý từ 2-3 món kèm theo lý do tại sao món đó phù hợp.
3. Nhắc đến ưu đãi nếu có (ví dụ: size L giá hời)."""


class ConsultantAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="consultant_agent", system_prompt=CONSULTANT_SYSTEM_PROMPT)

    async def process(
        self, query: str, session_history: list[dict], session_id: str | None = None
    ) -> str:
        store = get_knowledge_store()
        neo4j = get_neo4j_client()
        query_lower = query.lower()

        # 1. Context Gathering: Mock Weather
        weather = random.choice(["nóng", "mát mẻ", "mưa", "lạnh"])
        
        # 2. Graph-based Recommendation
        # If user asks for a category or characteristic, we use Graph
        category_target = None
        if "cà phê" in query_lower or "phin" in query_lower: category_target = "Cà Phê"
        elif "trà" in query_lower: category_target = "Trà"
        elif "freeze" in query_lower or "đá xay" in query_lower: category_target = "Freeze"

        try:
            if category_target:
                graph_items = await neo4j.get_recommendations_by_category(category_target)
                # Convert back to MenuItem objects
                expanded_results = [store.menu_items[0]] # placeholder logic for format_menu_items compatibility
                # Simplified for this update:
                expanded_results = store.search_menu(category_target, top_k=5)
            else:
                expanded_results = store.search_hybrid(query, domain="menu", top_k=4)
                expanded_results = store.expand_graph(expanded_results)
        except Exception:
            expanded_results = store.search_menu(query, top_k=5)
        
        if not expanded_results:
            # Fallback to popular items if no match
            expanded_results = store.search_menu("phin sữa freeze trà sen", top_k=5)

        # 4. Contextual Filtering & Response Building
        intro = self._get_contextual_intro(weather, query_lower)
        menu_text = store.format_menu_items(expanded_results[:5])
        
        response = f"{intro}\n\nDựa trên yêu cầu của bạn, mình gợi ý các món sau:\n{menu_text}\n\n"
        
        # Add a specific tip based on context
        if "rẻ" in query_lower or "tiết kiệm" in query_lower:
            response += "💡 Tip: Các dòng Phin truyền thống đang có giá rất tốt chỉ từ 29k đấy ạ!"
        elif weather == "nóng":
            response += "🧊 Tip: Bạn nên chọn dòng Freeze để giải nhiệt tức thì nhé!"
        elif "mệt" in query_lower or "tỉnh táo" in query_lower:
            response += "⚡ Tip: Một ly Phin Đen Đá đậm đà sẽ giúp bạn lấy lại năng lượng nhanh nhất!"
        else:
            response += "😊 Bạn có muốn mình tư vấn chi tiết hơn về món nào không?"

        return response

    def _get_contextual_intro(self, weather: str, query: str) -> str:
        """Generate a friendly intro based on weather/context."""
        if "chào" in query:
            return "Chào bạn! Rất vui được tư vấn đồ uống cho bạn."
            
        intros = {
            "nóng": "Trời hôm nay khá nóng nực, một ly đồ uống mát lạnh sẽ là lựa chọn tuyệt vời! ☀️",
            "mát mẻ": "Thời tiết hôm nay thật dễ chịu, rất thích hợp để thưởng thức một ly trà hoặc cà phê thong thả. ☁️",
            "mưa": "Trời đang mưa, một ly cà phê ấm nóng hoặc trà sen thơm ngát sẽ giúp bạn thấy thư giãn hơn. 🌧️",
            "lạnh": "Thời tiết se lạnh thế này, còn gì bằng một ly Phin Sữa Nóng đậm đà bạn nhỉ? ❄️"
        }
        return intros.get(weather, "Rất vui được hỗ trợ bạn chọn món ngon tại Highlands!")
