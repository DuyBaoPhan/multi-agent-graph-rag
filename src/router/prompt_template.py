"""
Router Prompt Template
========================
Structured prompt for intent classification (Module A1.1).
Ensures JSON output format: {"action": "<intent>"}
"""

ROUTER_SYSTEM_PROMPT = """Bạn là bộ phân loại intent cho hệ thống đặt đồ uống Highlands Coffee.

Phân loại câu hỏi của khách hàng vào ĐÚNG 1 trong 4 intent sau:
- "order": Khách muốn đặt đồ uống, hỏi giá, hỏi menu, thêm/bớt món
- "faq": Khách hỏi về chính sách, giờ mở cửa, địa chỉ, khuyến mãi, thông tin chung
- "consultant": Khách cần tư vấn chọn đồ uống phù hợp, so sánh, gợi ý
- "chitchat": Chào hỏi, cảm ơn, tạm biệt, nói chuyện phiếm

Trả lời CHÍNH XÁC theo JSON format, không thêm bất kỳ text nào khác."""

ROUTER_USER_TEMPLATE = """Câu hỏi: {query}

Output:"""

ROUTER_FEW_SHOT_EXAMPLES = [
    {"query": "Cho tôi một ly Phở đi Freeze size L", "output": '{"action": "order"}'},
    {"query": "Highlands mở cửa mấy giờ?", "output": '{"action": "faq"}'},
    {"query": "Nên uống gì cho mát vào mùa hè?", "output": '{"action": "consultant"}'},
    {"query": "Cảm ơn bạn nhé!", "output": '{"action": "chitchat"}'},
    {"query": "Có gì vừa ngon vừa rẻ không?", "output": '{"action": "consultant"}'},
]


def build_router_prompt(query: str, use_few_shot: bool = True) -> list[dict]:
    """
    Build the complete prompt for intent classification.
    
    Args:
        query: User's input query
        use_few_shot: Whether to include few-shot examples
        
    Returns:
        List of message dicts for the LLM API
    """
    messages = [{"role": "system", "content": ROUTER_SYSTEM_PROMPT}]

    if use_few_shot:
        for example in ROUTER_FEW_SHOT_EXAMPLES:
            messages.append({
                "role": "user",
                "content": ROUTER_USER_TEMPLATE.format(query=example["query"]),
            })
            messages.append({"role": "assistant", "content": example["output"]})

    messages.append({
        "role": "user",
        "content": ROUTER_USER_TEMPLATE.format(query=query),
    })

    return messages
