"""
Order Agent — Module A2.1 (Hardened)
====================================
Handles ordering with AI extraction and Redis session persistence.
"""

import json
from loguru import logger

from src.agents.base_agent import BaseAgent
from src.graph_rag.knowledge_store import get_knowledge_store, MenuItem
from src.graph_rag.neo4j_client import get_neo4j_client
from src.agents.session_store import get_session_store

ORDER_SYSTEM_PROMPT = """Bạn là nhân viên phục vụ Highlands Coffee. 
Nhiệm vụ: Giúp khách xem menu, thêm món vào giỏ hàng, xóa món và tính tổng tiền.
Quy tắc:
1. Chỉ bán món có trong menu.
2. Khi khách hỏi về giỏ hàng hoặc tổng tiền, liệt kê chi tiết và tổng cộng.
3. Không bao giờ tự bịa ra món ăn."""

class OrderAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="order_agent", system_prompt=ORDER_SYSTEM_PROMPT)

    async def process(self, query: str, session_history: list[dict], session_id: str | None = None) -> str:
        store = get_knowledge_store()
        neo4j = get_neo4j_client()
        session_store = get_session_store()
        query_lower = query.lower()

        # 1. Get Cart from Redis (CRITICAL FIX)
        metadata = await session_store.get_metadata_async(session_id)
        cart = metadata.get("cart", [])

        # Case A: View Cart / Billing (Improved Keywords)
        billing_keywords = ["giỏ hàng", "đã đặt", "xem đơn", "tính tiền", "hóa đơn", "bill", "tổng", "bao nhiêu", "tiền"]
        if any(kw in query_lower for kw in billing_keywords) and not any(kw in query_lower for kw in ["thêm", "cho", "lấy", "đặt"]):
            if not cart:
                return "Dạ, giỏ hàng của mình đang trống ạ. Anh chị muốn dùng gì để em thêm vào ạ?"
            
            bill_lines = [f"- {item['name']} ({item['size']}) x{item['quantity']}: {item['price']*item['quantity']:,}đ" for item in cart]
            total = sum(item['price'] * item['quantity'] for item in cart)
            return f"Dạ, giỏ hàng hiện tại của mình có:\n" + "\n".join(bill_lines) + f"\n\n👉 Tổng cộng: {total:,}đ ạ. Anh chị muốn đặt thêm gì nữa không?"

        # Case B: Remove Item
        if any(kw in query_lower for kw in ["xóa", "bỏ", "hủy"]):
            for i, item in enumerate(cart):
                if item["name"].lower() in query_lower:
                    removed = cart.pop(i)
                    await session_store.update_metadata(session_id, {"cart": cart})
                    return f"Dạ, em đã xóa {removed['name']} khỏi giỏ hàng rồi ạ."

        # Case C: Add Item (AI Extraction)
        extraction_prompt = f"""Dựa trên yêu cầu của khách: '{query}', hãy trích xuất danh sách các món đồ uống/thức ăn.
Trả về duy nhất JSON list: [{{"name": "tên món", "quantity": số lượng, "size": "S/M/L hoặc null"}}]
Ví dụ: "2 ly phin sữa đá size M" -> [{{"name": "Phin Sữa Đá", "quantity": 2, "size": "M"}}]"""
        
        try:
            extraction_raw = await self.llm.generate([
                {"role": "system", "content": "Bạn là chuyên gia bóc tách đơn hàng. Chỉ trả về JSON."},
                {"role": "user", "content": extraction_prompt}
            ])
            items_to_add = json.loads(extraction_raw.strip().replace("```json", "").replace("```", ""))
        except:
            items_to_add = [{"name": query_lower, "quantity": 1, "size": None}]

        added_summary = []
        for item_data in items_to_add:
            name = item_data.get("name", "")
            quantity = item_data.get("quantity", 1)
            size_target = item_data.get("size", "M") # Default to M if not specified
            
            # Search menu
            menu_items = await neo4j.graph_search_menu(name, top_k=5)
            if not menu_items:
                menu_items = store.search_menu(name, top_k=5)
            else:
                # Convert Graph records to objects
                menu_items = [MenuItem(name=r['p']['name'], price=r['p']['price'], size=r['p']['size'], category=r['category']) for r in menu_items]

            if not menu_items: continue

            # Find best match for size
            best_match = menu_items[0]
            if size_target:
                for m in menu_items:
                    if str(m.size).upper() == str(size_target).upper():
                        best_match = m
                        break
            
            cart.append({
                "name": best_match.name,
                "size": best_match.size,
                "price": best_match.price,
                "quantity": quantity
            })
            added_summary.append(f"{quantity} {best_match.name} ({best_match.size})")

        if not added_summary:
            return "Dạ, em chưa rõ món anh chị muốn đặt. Mình vui lòng nói rõ tên món và số lượng giúp em nhé!"

        await session_store.update_metadata(session_id, {"cart": cart})
        return f"Dạ, em đã thêm {', '.join(added_summary)} vào giỏ hàng rồi ạ. Anh chị có muốn dùng thêm gì nữa không ạ?"
