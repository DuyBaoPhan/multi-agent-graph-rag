"""
Consultant Agent — Module A2.1 (Upgraded)
========================================
Personalized drink recommendations using Context-aware Hybrid RAG.
Considers: Taste, Budget, Weather, and Health.
"""

import random
from loguru import logger
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
        
        # 3. Handle Context (History)
        history_text = " ".join([msg["content"].lower() for msg in session_history[-2:]])
        combined_query = f"{history_text} {query_lower}".strip()

        # If user asks for category in query OR history
        category_target = None
        if any(w in combined_query for w in ["cà phê", "phin", "cafe", "coffee", "café"]): category_target = "Cà Phê"
        elif "trà" in combined_query: category_target = "Trà"
        elif "freeze" in combined_query or "đá xay" in combined_query: category_target = "Freeze"

        try:
            if category_target:
                graph_items = await neo4j.get_recommendations_by_category(category_target)
                expanded_results = []
                for r in graph_items:
                    item = store.get_item_by_name(r['name'])
                    if item:
                        expanded_results.append(item)
            else:
                expanded_results = store.search_hybrid(combined_query, domain="menu", top_k=2)
                expanded_results = store.expand_graph(expanded_results)
        except Exception:
            expanded_results = store.search_menu(combined_query, top_k=2)
        
        if not expanded_results:
            expanded_results = store.search_menu("phin sữa", top_k=2)

        # 4. Concise Response Building
        intro = "Dạ, mình gợi ý vài món bán chạy nhất nhé:" if not category_target else f"Dạ, về dòng {category_target}, mình gợi ý món này ạ:"
        menu_text = store.format_menu_items(expanded_results[:2])
        
        response = f"{intro}\n{menu_text}\n\n👉 Bạn muốn đặt món nào ạ?"
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
