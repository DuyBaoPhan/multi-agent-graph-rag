"""
Fallback Handler
==================
Graceful degradation when services are overloaded (Module C3).
"""

from loguru import logger

FALLBACK_RESPONSES = {
    "order": "Xin lỗi, hệ thống đặt hàng đang bận. Vui lòng thử lại sau ít phút hoặc gọi hotline 1900-xxxx.",
    "faq": "Xin lỗi, tôi chưa thể tra cứu thông tin lúc này. Vui lòng thử lại sau.",
    "consultant": "Xin lỗi, dịch vụ tư vấn đang tạm ngưng. Vui lòng thử lại sau.",
    "chitchat": "Xin lỗi, tôi đang bận chút. Bạn vui lòng chờ một lát nhé!",
    "default": "Xin lỗi, hệ thống đang quá tải. Vui lòng thử lại sau ít phút.",
}


def get_fallback_response(intent: str = "default") -> str:
    """
    Get a fallback response when the main pipeline fails.
    
    Args:
        intent: The classified intent (for intent-specific fallbacks)
        
    Returns:
        Fallback response string
    """
    response = FALLBACK_RESPONSES.get(intent, FALLBACK_RESPONSES["default"])
    logger.warning(f"Using fallback response for intent: {intent}")
    return response
