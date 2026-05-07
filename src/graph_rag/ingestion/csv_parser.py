"""
CSV Parser
=============
Parse CSV files for menu items and FAQ data (Module B1.3).
"""

import csv
from pathlib import Path

from loguru import logger


def parse_menu_csv(filepath: str | Path) -> list[dict]:
    """
    Parse a CSV file containing menu items.
    
    Expected columns: name, price, size, category, description
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        List of menu item dicts
    """
    items = []
    filepath = Path(filepath)

    if not filepath.exists():
        logger.error(f"Menu CSV not found: {filepath}")
        return items

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append({
                "name": row.get("name", "").strip(),
                "price": int(row.get("price", 0)),
                "size": row.get("size", "M").strip(),
                "category": row.get("category", "").strip(),
                "description": row.get("description", "").strip(),
            })

    logger.info(f"Parsed {len(items)} menu items from {filepath.name}")
    return items


def parse_faq_csv(filepath: str | Path) -> list[dict]:
    """
    Parse a CSV file containing FAQ entries.
    
    Expected columns: question, answer, category
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        List of FAQ entry dicts
    """
    faqs = []
    filepath = Path(filepath)

    if not filepath.exists():
        logger.error(f"FAQ CSV not found: {filepath}")
        return faqs

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            faqs.append({
                "question": row.get("question", "").strip(),
                "answer": row.get("answer", "").strip(),
                "category": row.get("category", "general").strip(),
            })

    logger.info(f"Parsed {len(faqs)} FAQ entries from {filepath.name}")
    return faqs
