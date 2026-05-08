"""
Agent Dispatcher — Module A2.1
================================
Routes intents to agents. Includes request queue with semaphore (A2.3).
"""

import asyncio
import uuid

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.agents.base_agent import BaseAgent
from src.agents.order_agent import OrderAgent
from src.agents.faq_agent import FAQAgent
from src.agents.consultant_agent import ConsultantAgent

# Request queue settings (Module A2.3)
_semaphore = asyncio.Semaphore(3)  # Max 3 concurrent LLM calls
_REQUEST_TIMEOUT = 60.0


class AgentDispatcher:
    """Dispatches queries to agents with concurrency control."""

    def __init__(self):
        self.agents: dict[str, BaseAgent] = {
            "order": OrderAgent(),
            "faq": FAQAgent(),
            "consultant": ConsultantAgent(),
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def dispatch(
        self, intent: str, query: str, session_history: list[dict], session_id: str | None = None
    ) -> str:
        if intent == "ignore":
            return self._handle_ignore(query)

        agent = self.agents.get(intent)
        if not agent:
            logger.warning(f"Unknown intent '{intent}', fallback to ignore")
            return self._handle_ignore(query)

        # Concurrency control with semaphore (Module A2.3)
        try:
            async with asyncio.timeout(_REQUEST_TIMEOUT):
                async with _semaphore:
                    logger.info(f"Dispatching to {agent.name} for intent '{intent}'")
                    return await agent.process(query, session_history, session_id)
        except TimeoutError:
            logger.error(f"Request timeout after {_REQUEST_TIMEOUT}s")
            return "Xin lỗi, yêu cầu đã hết thời gian chờ. Vui lòng thử lại."

    def _handle_ignore(self, query: str) -> str:
        q = query.lower()
        is_english = any(w in q for w in ["hello", "hi", "hey", "thank", "bye"]) and not any(w in q for w in ["chào", "cảm ơn", "tạm biệt"])

        if is_english:
            if any(w in q for w in ["hello", "hi", "hey"]):
                return "Hello! 👋 I'm the Highlands Coffee assistant. I can help you order drinks, view the menu, or answer your questions. How can I help you today?"
            if "thank" in q:
                return "You're welcome! ☕ Happy to help. See you again!"
            if "bye" in q:
                return "Goodbye! 👋 Have a great day. Highlands Coffee is always here for you!"
            if any(w in q for w in ["name", "who", "bot"]):
                return "I'm the Highlands Coffee chatbot assistant 🤖. I can help you with the menu, ordering, and any questions!"
            return "Thank you for sharing! ☕ How can I help you today?"

        if any(w in q for w in ["chào", "hello", "hi ", "xin chào"]):
            return "Xin chào! 👋 Tôi là trợ lý Highlands Coffee. Tôi có thể giúp bạn đặt đồ uống, trả lời câu hỏi, hoặc tư vấn món ngon. Bạn muốn gì nào?"
        if any(w in q for w in ["cảm ơn", "thank"]):
            return "Không có gì ạ! ☕ Rất vui được phục vụ bạn. Hẹn gặp lại!"
        if any(w in q for w in ["tạm biệt", "bye"]):
            return "Tạm biệt bạn! 👋 Chúc bạn một ngày tốt lành. Highlands Coffee luôn sẵn sàng phục vụ!"
        if any(w in q for w in ["tên", "ai", "bot"]):
            return "Tôi là chatbot trợ lý của Highlands Coffee 🤖. Tôi có thể giúp bạn xem menu, đặt hàng, và trả lời mọi thắc mắc!"
        return "Cảm ơn bạn đã chia sẻ! ☕ Tôi có thể giúp bạn đặt đồ uống hoặc trả lời câu hỏi về Highlands Coffee. Bạn muốn thử gì?"
