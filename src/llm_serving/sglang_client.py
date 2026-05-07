"""
SGLang Client
===============
OpenAI-compatible client for SGLang server (Module B2.1).
"""

import httpx
from loguru import logger

from src.config import get_settings


class SGLangClient:
    """
    Async client for SGLang inference server.
    
    Supports both Router (classification) and Generator (response) models
    via OpenAI-compatible API.
    """

    def __init__(self, base_url: str, model_name: str = "default"):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

    async def chat_completion(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> dict | None:
        """
        Call SGLang chat completion endpoint.
        
        Args:
            messages: List of message dicts
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream response
            
        Returns:
            Response dict or None on error
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": stream,
                },
            )
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        """Check if the SGLang server is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


def get_router_client() -> SGLangClient:
    """Get SGLang client for Router model."""
    settings = get_settings()
    return SGLangClient(settings.sglang_router_host, "router")


def get_generator_client() -> SGLangClient:
    """Get SGLang client for Generator model."""
    settings = get_settings()
    return SGLangClient(settings.sglang_generator_host, "generator")
