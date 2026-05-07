"""
Intent Extractor
==================
SLM-based intent extraction for semantic cache keys (Module C2.1).
Fine-tuned Qwen3-0.6B splits queries into: subject, action, context.
"""

from loguru import logger


async def extract_cache_components(query: str) -> dict:
    """
    Extract structured components from a query for cache key generation.
    
    Output format:
    {
        "subject": "khách hàng",
        "action": "hỏi giá cà phê sữa",   # → cache key
        "context": "size L, ít đường"        # → sent to agent
    }
    
    Args:
        query: User's input query
        
    Returns:
        Dict with subject, action, context
    """
    # TODO: Call fine-tuned Qwen3-0.6B for structured extraction
    # TODO: Parse JSON output
    logger.debug(f"Extracting cache components from: {query[:50]}...")
    return {
        "subject": "",
        "action": query,
        "context": "",
    }
