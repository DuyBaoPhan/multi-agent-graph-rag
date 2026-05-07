"""
Router Serving
================
SGLang client for intent classification (Module A1.1).
Sends queries to the fine-tuned Router AWQ model.
"""

import json

import httpx
from loguru import logger

from src.config import get_settings
from src.router.prompt_template import build_router_prompt

VALID_INTENTS = {"order", "faq", "consultant", "chitchat"}


async def classify_intent(query: str) -> dict:
    """
    Classify user query into one of 4 intents using the Router model.
    
    Args:
        query: User's input text
        
    Returns:
        Dict with 'action' key, e.g. {"action": "order"}
        
    Raises:
        ValueError: If the model returns invalid JSON or unknown intent
    """
    settings = get_settings()
    messages = build_router_prompt(query)

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.sglang_router_host}/v1/chat/completions",
            json={
                "model": "router",
                "messages": messages,
                "max_tokens": 20,
                "temperature": 0.0,
            },
        )
        response.raise_for_status()

    result_text = response.json()["choices"][0]["message"]["content"].strip()

    try:
        result = json.loads(result_text)
    except json.JSONDecodeError:
        logger.warning(f"Router returned invalid JSON: {result_text}")
        # Fallback: try to extract intent from text
        for intent in VALID_INTENTS:
            if intent in result_text.lower():
                return {"action": intent}
        return {"action": "chitchat"}  # Safe default

    action = result.get("action", "chitchat")
    if action not in VALID_INTENTS:
        logger.warning(f"Router returned unknown intent: {action}")
        action = "chitchat"

    return {"action": action}
