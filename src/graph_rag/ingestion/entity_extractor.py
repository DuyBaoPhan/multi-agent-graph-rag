"""
Entity Extractor
==================
Extract named entities from text chunks using LLM (Module B1.3).
"""

from loguru import logger


async def extract_entities(text: str, llm_client=None) -> list[dict]:
    """
    Extract entities from a text chunk using LLM.
    
    Entity types: DRINK, INGREDIENT, LOCATION, BRAND, PROMOTION
    
    Args:
        text: Text chunk to extract entities from
        llm_client: LLM client for entity extraction
        
    Returns:
        List of entity dicts with 'name', 'type', 'confidence'
    """
    # TODO: Call LLM with entity extraction prompt
    # TODO: Parse structured JSON output
    logger.debug(f"Entity extraction from chunk ({len(text)} chars)")
    return []
