"""
Base Agent
============
Abstract base class for all agents (Module A2.1).
"""

from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    Abstract base class for specialized agents.
    
    Each agent has:
    - A unique system prompt defining its role
    - A set of tools it can call
    - Access to session history
    """

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt

    @abstractmethod
    async def process(
        self, query: str, session_history: list[dict], session_id: str | None = None
    ) -> str:
        """
        Process a user query and return a response.
        
        Args:
            query: User's input text
            session_history: List of previous conversation turns
            
        Returns:
            Agent's response text
        """
        pass

    def build_messages(self, query: str, session_history: list[dict]) -> list[dict]:
        """Build message list with system prompt, history, and current query."""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(session_history)
        messages.append({"role": "user", "content": query})
        return messages
