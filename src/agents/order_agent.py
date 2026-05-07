"""
Order Agent — Module A2.1 (Upgraded)
====================================
Handles ordering, menu queries, cart management (add/remove), and billing.
Uses KnowledgeStore for menu data and SessionStore for cart state.
"""

import re
from loguru import logger

from src.agents.base_agent import BaseAgent
from src.graph_rag.knowledge_store import get_knowledge_store, MenuItem
from src.graph_rag.neo4j_client import get_neo4j_client
from src.agents.session_store import get_session_store

ORDER_SYSTEM_PROMPT = """Bạn là nhân viên phục vụ Highlands Coffee. 
Nhiệm vụ: Giúp khách xem menu, thêm món vào giỏ hàng, xóa món và tính tổng tiền.
Quy tắc:
1. Chỉ bán món có trong menu.
2. Luôn xác nhận lại tên món và số lượng.
3. Khi tính tiền, liệt kê chi tiết và tổng cộng."""


class OrderAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="order_agent", system_prompt=ORDER_SYSTEM_PROMPT)

    async def process(
        self, query: str, session_history: list[dict], session_id: str | None = None
    ) -> str:
        # 0. Get Clients
        store = get_knowledge_store()
        neo4j = get_neo4j_client()
        session_store = get_session_store()
        query_lower = query.lower()

        # 1. Get or Init Cart
        metadata = session_store.get_metadata(session_id) if session_id else {"cart": []}
        cart = metadata.get("cart", [])

        # --- Handle Actions ---

        # Case A: View Cart / Billing
        if any(kw in query_lower for kw in ["giỏ hàng", "đã đặt", "xem đơn", "tính tiền", "hóa đơn", "bill"]):
            if not cart:
                return "Dạ, giỏ hàng của mình đang trống ạ. Anh chị muốn dùng gì để em thêm vào ạ?"
            
            bill_lines = [f"- {item['name']} ({item['size']}) x{item['quantity']}: {item['price']*item['quantity']:,}đ" for item in cart]
            total = sum(item['price'] * item['quantity'] for item in cart)
            
            if any(kw in query_lower for kw in ["tính tiền", "hóa đơn", "bill"]):
                return f"Dạ, đây là hóa đơn của mình ạ:\n" + "\n".join(bill_lines) + f"\n\n👉 Tổng cộng: {total:,}đ. Anh chị muốn thanh toán bằng tiền mặt hay chuyển khoản ạ?"
            return "Dạ, giỏ hàng hiện tại của mình có:\n" + "\n".join(bill_lines) + f"\n\nTổng cộng: {total:,}đ ạ."

        # Case B: Remove Item
        if any(kw in query_lower for kw in ["xóa", "bỏ", "hủy"]):
            # Simple heuristic: look for item name in query
            for i, item in enumerate(cart):
                if item["name"].lower() in query_lower:
                    removed = cart.pop(i)
                    session_store.update_metadata(session_id, {"cart": cart})
                    return f"Dạ, em đã xóa {removed['name']} khỏi giỏ hàng rồi ạ. Mình có muốn gọi thêm gì nữa không ạ?"
            return "Dạ, em không thấy món này trong giỏ hàng. Anh chị kiểm tra lại giúp em nhé."

        # Case C: Add Item (Search RAG)
        # 1. Try to find quantity
        qty_match = re.search(r"(\d+)", query)
        quantity = int(qty_match.group(1)) if qty_match else 1

        # 2. Try to find size (S, M, L)
        size_target = None
        if "size l" in query_lower or "size to" in query_lower or "ly lớn" in query_lower:
            size_target = "L"
        elif "size m" in query_lower or "size vừa" in query_lower or "ly vừa" in query_lower:
            size_target = "M"
        elif "size s" in query_lower or "size nhỏ" in query_lower or "ly nhỏ" in query_lower:
            size_target = "S"

        # 3. Try to find item name by stripping action keywords
        clean_query = re.sub(r"(cho|lấy|đặt|thêm|order|mua|gọi|bán|có|còn|\d+|size|ly|cốc|l\b|m\b|s\b)", "", query_lower).strip()
        
        # 4. Search menu for best match (Graph RAG priority)
        try:
            # Attempt Graph Search first
            graph_results = await neo4j.graph_search_menu(clean_query, top_k=5)
            if graph_results:
                items = [MenuItem(
                    name=r['p']['name'], 
                    price=r['p']['price'], 
                    size=r['p']['size'], 
                    category=r['category'],
                    description=r['p'].get('description', '')
                ) for r in graph_results]
            else:
                items = store.search_menu(clean_query, top_k=10)
        except Exception as e:
            logger.warning(f"Neo4j search failed, falling back to KnowledgeStore: {e}")
            items = store.search_menu(clean_query, top_k=10)

        if not items:
            return f"Dạ, em nghe không rõ tên món. Anh chị muốn 'thêm' món gì cụ thể không ạ? (Ví dụ: 2 bạc xỉu)"

        # 5. Filter by size if requested
        best_match = items[0]
        if size_target:
            size_matches = [i for i in items if i.size == size_target]
            if size_matches:
                best_match = size_matches[0]
        
        # 6. Add to cart
        cart.append({
            "name": best_match.name,
            "size": best_match.size,
            "price": best_match.price,
            "quantity": quantity
        })
        session_store.update_metadata(session_id, {"cart": cart})
        
        return f"Dạ, em đã thêm {quantity} {best_match.name} size {best_match.size} vào giỏ hàng rồi ạ. Anh chị có muốn dùng thêm gì nữa không ạ?"
