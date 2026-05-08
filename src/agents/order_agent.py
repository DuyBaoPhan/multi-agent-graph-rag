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
        billing_keywords = ["giỏ hàng", "đã đặt", "xem đơn", "tính tiền", "hóa đơn", "bill", "tổng", "bao nhiêu", "tiền", "order những gì", "đã order"]
        is_view_cart = any(kw in query_lower for kw in billing_keywords)
        
        # Determine if user is actually trying to ADD items despite using a billing keyword 
        # (e.g. "thêm 1", "cho 2 ly")
        import re
        is_adding_item = bool(re.search(r'\b(thêm|cho|lấy|đặt|mua)\s+\d+\b', query_lower)) or \
                         bool(re.search(r'\b(size|cỡ)\s+[sml]\b', query_lower)) or \
                         bool(re.search(r'\b(thêm|lấy)\s+(bánh|trà|cà phê|phindi|freeze)\b', query_lower))

        if is_view_cart and not is_adding_item:
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
        from src.llm_serving.sglang_client import get_generator_client
        import re
        
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in session_history[-4:]])
        
        extraction_prompt = f"""Lịch sử chat gần đây:
{history_text}

Dựa trên yêu cầu HIỆN TẠI của khách: '{query}', hãy trích xuất danh sách các món MỚI mà khách muốn thêm.
QUAN TRỌNG: 
1. CHỈ trích xuất món mới được yêu cầu TRONG CÂU HỎI HIỆN TẠI. 
2. Tuyệt đối KHÔNG trích xuất lại các món đã được nhắc đến trong lịch sử chat trừ khi khách nói rõ là muốn thêm nữa.
3. Nếu khách nói 'như trên', 'giống vậy' thì mới nhìn vào lịch sử.
Trả về duy nhất JSON list: [{{"name": "tên món", "quantity": số lượng, "size": "S/M/L hoặc null"}}]
Ví dụ: "2 ly phin sữa đá size M" -> [{{"name": "Phin Sữa Đá", "quantity": 2, "size": "M"}}]"""
        
        try:
            # SGLang Client (Primary)
            llm = get_generator_client()
            extraction_raw = await llm.chat_completion([
                {"role": "system", "content": "Bạn là chuyên gia bóc tách đơn hàng. Chỉ trả về JSON array."},
                {"role": "user", "content": extraction_prompt}
            ], max_tokens=200)
            content = extraction_raw["choices"][0]["message"]["content"]
            json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
            if json_match:
                items_to_add = json.loads(json_match.group(0))
            else:
                content = content.strip().replace("```json", "").replace("```", "").strip()
                items_to_add = json.loads(content)
        except Exception as e1:
            logger.warning(f"Primary extraction failed: {e1}. Trying LM Studio/API fallback...")
            try:
                # Try LM Studio / API directly as fallback
                import httpx, os
                lm_studio_host = os.getenv("LM_STUDIO_HOST", "http://127.0.0.1:1234")
                messages = [
                    {"role": "system", "content": "Bạn là chuyên gia bóc tách đơn hàng. Chỉ trả về JSON array hợp lệ. Không giải thích."},
                    {"role": "user", "content": extraction_prompt}
                ]
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{lm_studio_host}/v1/chat/completions",
                        json={"model": "local-model", "messages": messages, "max_tokens": 200, "temperature": 0.1}
                    )
                    resp.raise_for_status()
                    content = resp.json()["choices"][0]["message"]["content"]
                    # Use regex to extract the JSON array, ignoring chatty text
                    json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
                    if json_match:
                        items_to_add = json.loads(json_match.group(0))
                    else:
                        # Try parsing the whole thing just in case
                        content = content.strip().replace("```json", "").replace("```", "").strip()
                        items_to_add = json.loads(content)
            except Exception as e2:
                logger.warning(f"Order extraction fallback triggered: {e2}")
                # Rule-based fallback (handles 1 item only)
                qty_match = re.search(r'\b(\d+)\b', query_lower)
                quantity = int(qty_match.group(1)) if qty_match else 1
                
                size_target = None
                if re.search(r'\b(size l|cỡ l|lớn|large)\b', query_lower): size_target = "L"
                elif re.search(r'\b(size s|cỡ s|nhỏ|small)\b', query_lower): size_target = "S"
                elif re.search(r'\b(size m|cỡ m|vừa|medium)\b', query_lower): size_target = "M"
                
                name_clean = query_lower
                for word in ["thêm", "cho", "mình", "tôi", "lấy", "bán", "đi", "nữa", "size s", "size m", "size l", "cỡ", "ly", "cốc", str(quantity)]:
                    name_clean = re.sub(rf'\b{word}\b', ' ', name_clean)
                
                name_clean = name_clean.strip()
                # Resolve common shorthands / context manually since LLM is offline
                shorthands = {
                    "choco": "phindi choco",
                    "hạnh nhân": "phindi hạnh nhân",
                    "sen vàng": "trà sen vàng",
                    "sữa đá": "phin sữa đá",
                    "bạc xỉu": "phindi sữa đá",
                    "bạc sỉu": "phindi sữa đá"
                }
                for short, full in shorthands.items():
                    if short in name_clean:
                        name_clean = name_clean.replace(short, full)
                        
                items_to_add = [{"name": name_clean, "quantity": int(quantity), "size": size_target}]

        if isinstance(items_to_add, dict):
            items_to_add = [items_to_add]
        elif not isinstance(items_to_add, list):
            items_to_add = []

        added_summary = []
        for item_data in items_to_add:
            name = str(item_data.get("name", "")).strip()
            quantity = int(item_data.get("quantity", 1))
            size_target = item_data.get("size", None) # Default to None to use best match
            
            if not name: continue

            # Search menu (Neo4j then local)
            menu_items = await neo4j.graph_search_menu(name, top_k=5)
            if not menu_items:
                menu_items = store.search_menu(name, top_k=5)
            else:
                # Convert Graph records to objects (Fix: include description)
                menu_items = [
                    MenuItem(
                        name=r['p']['name'], 
                        price=int(r['p']['price']), 
                        size=r['p']['size'], 
                        category=r['category'],
                        description=r['p'].get('description', '')
                    ) for r in menu_items
                ]

            if not menu_items: continue

            # Find best match (exact name match first, then size match)
            best_match = menu_items[0]
            # Try to find exact name match first among candidates
            for m in menu_items:
                if m.name.lower() == name.lower():
                    best_match = m
                    break
            
            # Then refine by size if specified
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
            size_str = f" ({best_match.size})" if best_match.size else ""
            added_summary.append(f"{quantity} {best_match.name}{size_str}")

        if not added_summary:
            return "Dạ, em chưa rõ món anh chị muốn đặt. Mình vui lòng nói rõ tên món và số lượng giúp em nhé!"

        await session_store.update_metadata(session_id, {"cart": cart})
        
        # Calculate new total to pass to generator
        total = sum(item['price'] * item['quantity'] for item in cart)
        return f"Dạ, em đã thêm {', '.join(added_summary)} vào giỏ hàng rồi ạ. Tổng bill hiện tại là {total:,}đ. Anh chị có muốn dùng thêm gì nữa không ạ?"
