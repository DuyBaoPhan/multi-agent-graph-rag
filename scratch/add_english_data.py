import json
import random
from pathlib import Path

DATA_PATH = Path("data/training/router/train_set.jsonl")

# English examples for each intent
EN_EXAMPLES = [
    {"text": "Give me a coffee milk with ice", "intent": "order", "label": 0},
    {"text": "How much is the Freeze Green Tea?", "intent": "order", "label": 0},
    {"text": "I want to order 2 lattes size L", "intent": "order", "label": 0},
    {"text": "What do you recommend for a hot day?", "intent": "consultant", "label": 1},
    {"text": "Suggest something low sugar please", "intent": "consultant", "label": 1},
    {"text": "Any cheap drinks here?", "intent": "consultant", "label": 1},
    {"text": "What is the wifi password?", "intent": "faq", "label": 2},
    {"text": "What are your opening hours?", "intent": "faq", "label": 2},
    {"text": "Do you have parking space?", "intent": "faq", "label": 2},
    {"text": "Hello there!", "intent": "ignore", "label": 3},
    {"text": "Thanks a lot", "intent": "ignore", "label": 3},
    {"text": "Goodbye", "intent": "ignore", "label": 3},
]

def add_english_data():
    if not DATA_PATH.exists():
        return
    
    with open(DATA_PATH, "a", encoding="utf-8") as f:
        for item in EN_EXAMPLES:
            # Add each example 5 times to balance a bit for this demo
            for _ in range(5):
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Added {len(EN_EXAMPLES)*5} English samples to training set.")

if __name__ == "__main__":
    add_english_data()
