"""
SSE Streaming
===============
Server-Sent Events streaming for token-by-token generation (Module B2.2).
"""

import json
from collections.abc import AsyncGenerator

import httpx
from loguru import logger

from src.config import get_settings


async def stream_chat_response(
    messages: list[dict],
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> AsyncGenerator[str, None]:
    """
    Stream chat response token-by-token from SGLang.
    
    Yields individual tokens as they are generated.
    Handles [DONE] signal correctly (not JSON-parsed).
    
    Args:
        messages: Chat messages
        max_tokens: Max tokens to generate
        temperature: Sampling temperature
        
    Yields:
        Individual tokens as strings
    """
    settings = get_settings()

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{settings.sglang_generator_host}/v1/chat/completions",
            json={
                "model": "generator",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue

                data = line[6:]  # Remove "data: " prefix

                # Handle [DONE] signal — do NOT json.parse this
                if data.strip() == "[DONE]":
                    break

                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    logger.debug(f"Skipping malformed chunk: {e}")
                    continue


def split_for_tts(text: str) -> list[str]:
    """
    Split text at sentence boundaries for TTS streaming.
    
    Splits at: . ? ! ;
    
    Args:
        text: Full response text
        
    Returns:
        List of clauses for TTS
    """
    import re
    clauses = re.split(r'(?<=[.?!;])\s+', text)
    return [c.strip() for c in clauses if c.strip()]
