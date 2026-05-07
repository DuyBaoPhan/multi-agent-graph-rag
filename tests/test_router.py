"""
Router Tests
===============
Test intent classification accuracy and latency (Module A1).
Target: ≥ 92% accuracy, ≤ 200ms latency.
"""

import pytest

from src.router.prompt_template import build_router_prompt


# 20 test cases covering all intents + hard samples
TEST_CASES = [
    # Order intent
    ("Cho tôi một ly Phin Sữa Đá size L", "order"),
    ("Bao nhiêu tiền một ly Freeze Trà Xanh?", "order"),
    ("Thêm một ly Bạc Xỉu nữa", "order"),
    ("Tôi muốn đặt 2 ly cà phê sữa", "order"),
    ("Menu có những gì?", "order"),
    # FAQ intent
    ("Highlands mở cửa mấy giờ?", "faq"),
    ("Có ship không?", "faq"),
    ("Chính sách đổi trả như nào?", "faq"),
    ("Địa chỉ chi nhánh quận 1?", "faq"),
    ("Có chương trình khuyến mãi gì không?", "faq"),
    # Consultant intent
    ("Nên uống gì cho mát?", "consultant"),
    ("So sánh Phin Sữa và Bạc Xỉu giúp tôi", "consultant"),
    ("Có gì vừa ngon vừa rẻ không?", "consultant"),
    ("Gợi ý đồ uống cho buổi sáng", "consultant"),
    ("Uống gì ít calo?", "consultant"),
    # Chitchat intent
    ("Xin chào!", "chitchat"),
    ("Cảm ơn bạn nhé", "chitchat"),
    ("Tạm biệt", "chitchat"),
    ("Bạn tên gì?", "chitchat"),
    ("Hôm nay trời đẹp quá", "chitchat"),
]


class TestRouterPrompt:
    """Test prompt template construction."""

    def test_build_prompt_with_few_shot(self):
        messages = build_router_prompt("Cho tôi một ly cà phê")
        assert len(messages) > 2  # system + few-shot + user
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"

    def test_build_prompt_without_few_shot(self):
        messages = build_router_prompt("Xin chào", use_few_shot=False)
        assert len(messages) == 2  # system + user

    def test_prompt_contains_query(self):
        query = "Giá Phin Sữa Đá bao nhiêu?"
        messages = build_router_prompt(query)
        assert query in messages[-1]["content"]


class TestRouterAccuracy:
    """Test Router classification accuracy (requires running SGLang)."""

    @pytest.mark.skip(reason="Requires running SGLang server")
    @pytest.mark.asyncio
    async def test_classification_accuracy(self):
        """Target: ≥ 92% accuracy on 20 test cases."""
        from src.router.serving import classify_intent

        correct = 0
        for query, expected in TEST_CASES:
            result = await classify_intent(query)
            if result["action"] == expected:
                correct += 1

        accuracy = correct / len(TEST_CASES)
        assert accuracy >= 0.92, f"Accuracy {accuracy:.2%} < 92%"
