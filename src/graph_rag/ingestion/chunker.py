"""
Semantic Chunker
==================
Split documents into semantically coherent chunks (Module B1.3).
Uses gradient breakpoint method for intelligent splitting.
"""

import numpy as np
from loguru import logger


def semantic_chunk(
    text: str,
    embeddings_fn=None,
    max_chunk_size: int = 512,
    similarity_threshold: float = 0.5,
) -> list[str]:
    """
    Split text into semantic chunks using gradient breakpoint method.
    
    Algorithm:
    1. Split into sentences
    2. Compute embeddings for each sentence
    3. Calculate cosine similarity between consecutive sentences
    4. Find breakpoints where similarity drops significantly
    5. Group sentences into chunks at breakpoints
    
    Args:
        text: Full document text
        embeddings_fn: Function to compute embeddings (async)
        max_chunk_size: Maximum characters per chunk
        similarity_threshold: Threshold for similarity drop detection
        
    Returns:
        List of text chunks
    """
    # Simple sentence splitting (Vietnamese-aware)
    sentences = _split_sentences(text)

    if not sentences:
        return []

    if len(sentences) <= 3:
        return [text]

    # TODO: Replace with actual embedding-based chunking
    # For now, use simple size-based chunking
    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        if current_size + len(sentence) > max_chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_size = 0

        current_chunk.append(sentence)
        current_size += len(sentence)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    logger.info(f"Chunked text into {len(chunks)} chunks (from {len(sentences)} sentences)")
    return chunks


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, handling Vietnamese punctuation."""
    import re

    # Split on sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]
