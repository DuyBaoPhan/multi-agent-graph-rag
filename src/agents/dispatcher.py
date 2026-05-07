"""
Agent Dispatcher
==================
Routes classified intents to the appropriate agent (Module A2.1).
"""

from loguru import logger

from src.agents.base_agent import BaseAgent
from src.agents.order_agent import OrderAgent
from src.agents.faq_agent import FAQAgent
from src.agents.consultant_agent import ConsultantAgent


class AgentDispatcher:
    """
    Dispatches queries to the correct agent based on Router intent.
    
    Intent → Agent mapping:
    - "order"      → OrderAgent
    - "faq"        → FAQAgent
    - "consultant" → ConsultantAgent
    - "chitchat"   → handled inline (no RAG needed)
    """

    def __init__(self):
        self.agents: dict[str, BaseAgent] = {
            "order": OrderAgent(),
            "faq": FAQAgent(),
            "consultant": ConsultantAgent(),
        }

    async def dispatch(
        self, intent: str, query: str, session_history: list[dict]
    ) -> str:
        """
        Dispatch query to the appropriate agent.
        
        Args:
            intent: Classified intent from Router
            query: User's input text
            session_history: Conversation history
            
        Returns:
            Agent's response text
        """
        if intent == "chitchat":
            return await self._handle_chitchat(query)

        agent = self.agents.get(intent)
        if not agent:
            logger.warning(f"Unknown intent '{intent}', falling back to chitchat")
            return await self._handle_chitchat(query)

        logger.info(f"Dispatching to {agent.name} for intent '{intent}'")
        return await agent.process(query, session_history)

    async def _handle_chitchat(self, query: str) -> str:
        """Handle chitchat without RAG pipeline."""
        # TODO: Call LLM generator directly with simple prompt
        return "Xin chào! Tôi là trợ lý Highlands Coffee. Tôi có thể giúp gì cho bạn?"
