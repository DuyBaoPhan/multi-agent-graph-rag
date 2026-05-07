"""
Data Generation Script
========================
Generate training data for Router intent classification (Module A1.2).
Uses LLM API to create 4000 samples across 4 intents.
"""

import json
import os
from pathlib import Path

from loguru import logger
from tqdm import tqdm

# Checkpoint file for resume capability
CHECKPOINT_FILE = Path("data/training/router/checkpoint.json")
OUTPUT_FILE = Path("data/training/router/intent_data.jsonl")

INTENTS = ["order", "faq", "consultant", "chitchat"]
SAMPLES_PER_INTENT = 1000


def load_checkpoint() -> dict:
    """Load generation progress checkpoint."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {intent: 0 for intent in INTENTS}


def save_checkpoint(progress: dict):
    """Save current generation progress."""
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(progress, f)


def generate_samples(intent: str, count: int, batch_size: int = 50) -> list[dict]:
    """
    Generate training samples for a specific intent using LLM API.
    
    Args:
        intent: Target intent label
        count: Number of samples to generate
        batch_size: Samples per API call
        
    Returns:
        List of {query, intent} dicts
    """
    # TODO: Implement actual LLM API call (Claude/GPT)
    # TODO: Include hard samples (~20% of total)
    logger.info(f"Generating {count} samples for intent '{intent}'...")
    samples = []
    return samples


def main():
    """Main data generation pipeline with checkpoint/resume."""
    progress = load_checkpoint()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    for intent in INTENTS:
        remaining = SAMPLES_PER_INTENT - progress[intent]
        if remaining <= 0:
            logger.info(f"Intent '{intent}' already complete ({progress[intent]} samples)")
            continue

        logger.info(f"Generating {remaining} more samples for '{intent}'...")
        samples = generate_samples(intent, remaining)

        # Append to output file
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")

        progress[intent] += len(samples)
        save_checkpoint(progress)

    logger.info(f"✅ Data generation complete. Total progress: {progress}")


if __name__ == "__main__":
    main()
