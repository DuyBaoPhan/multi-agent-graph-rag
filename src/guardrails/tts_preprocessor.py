"""
TTS Preprocessor
==================
Normalize text for Text-to-Speech output (Module C3).
Converts prices, numbers, and special formats to spoken Vietnamese.
"""

import re


def preprocess_for_tts(text: str) -> str:
    """
    Preprocess text for TTS output.
    
    Conversions:
    - 49.000đ → "49 nghìn đồng"
    - 49k → "49 nghìn"
    - 120.000đ → "120 nghìn đồng"
    - 1.500.000đ → "1 triệu 500 nghìn đồng"
    
    Args:
        text: Raw text with prices/numbers
        
    Returns:
        TTS-friendly text
    """
    # Convert "XX.000đ" format
    text = re.sub(
        r'(\d{1,3})\.000đ',
        lambda m: f"{m.group(1)} nghìn đồng",
        text,
    )

    # Convert "XXk" format
    text = re.sub(
        r'(\d+)k\b',
        lambda m: f"{m.group(1)} nghìn",
        text,
        flags=re.IGNORECASE,
    )

    # Convert remaining "đ" currency
    text = re.sub(
        r'(\d[\d.]*)\s*đ\b',
        lambda m: f"{m.group(1).replace('.', '')} đồng",
        text,
    )

    return text
