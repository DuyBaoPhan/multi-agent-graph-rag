"""
Input Validator
=================
Validate and sanitize user input (Module C3).
"""

import re

from loguru import logger

# Maximum input length (characters)
MAX_INPUT_LENGTH = 1000

# Patterns that should be blocked
BLOCKED_PATTERNS = [
    r'(?i)ignore\s+previous\s+instructions',
    r'(?i)system\s*prompt',
    r'(?i)jailbreak',
]


def validate_input(text: str) -> tuple[bool, str]:
    """
    Validate user input for safety.
    
    Args:
        text: Raw user input
        
    Returns:
        Tuple of (is_valid, sanitized_text_or_error_message)
    """
    if not text or not text.strip():
        return False, "Input cannot be empty"

    if len(text) > MAX_INPUT_LENGTH:
        return False, f"Input too long (max {MAX_INPUT_LENGTH} characters)"

    # Check for blocked patterns (prompt injection attempts)
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, text):
            logger.warning(f"Blocked input matching pattern: {pattern}")
            return False, "Invalid input detected"

    # Sanitize: strip excessive whitespace
    sanitized = " ".join(text.split())

    return True, sanitized
