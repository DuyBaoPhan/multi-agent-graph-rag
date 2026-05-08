"""
Data Generation Pipeline — Module A1.2
========================================
Sinh 4000 samples intent classification dùng LLM API.
- 1000 samples mỗi intent: order / faq / consultant / ignore
- ~20% hard samples để tăng độ khó
- Checkpoint/resume để tránh mất data khi bị ngắt

Cách chạy:
    python scripts/generate_data.py --api anthropic --key YOUR_KEY
    python scripts/generate_data.py --api openai   --key YOUR_KEY
    python scripts/generate_data.py --demo          # sinh 40 mẫu offline (test)
"""

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

from loguru import logger

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR       = Path("data/training/router")
OUTPUT_FILE    = DATA_DIR / "intent_data.jsonl"
CHECKPOINT_FILE = DATA_DIR / "checkpoint.json"
TEST_SPLIT_FILE = DATA_DIR / "test_set.jsonl"
TRAIN_SPLIT_FILE = DATA_DIR / "train_set.jsonl"
VAL_SPLIT_FILE  = DATA_DIR / "val_set.jsonl"

INTENTS = ["order", "consultant", "faq", "ignore"]
INTENT_LABELS = {
    "order": 0,
    "consultant": 1,
    "faq": 2,
    "ignore": 3
}
SAMPLES_PER_INTENT = 1000
HARD_SAMPLE_RATIO  = 0.22   # ~22% hard samples

# ─── Prompt Templates ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Bạn là chuyên gia tạo dữ liệu training cho chatbot Highlands Coffee.
Nhiệm vụ: Tạo các câu hỏi/câu nói của khách hàng theo đúng intent yêu cầu.
Output: JSON array, mỗi phần tử là {"text": "câu hỏi", "intent": "intent_name"}
Chỉ output JSON, không thêm giải thích."""

INTENT_PROMPTS = {
    "order": """Tạo {n} câu khách hàng ĐẶT ĐỒ UỐNG / HỎI MENU / HỎI GIÁ tại Highlands Coffee.
Intent: "order"
Đa dạng về: size (S/M/L), tên món, số lượng, topping, yêu cầu đặc biệt.
Ví dụ dễ: "Cho 1 ly cà phê sữa đá size L", "Bạc Xỉu bao nhiêu tiền?"
Ví dụ khó (hard): "Còn món nào dưới 30k không?", "Cái nào ngon nhất?", "Menu hôm nay có gì mới?" """,

    "faq": """Tạo {n} câu khách hàng HỎI THÔNG TIN về Highlands Coffee.
Intent: "faq"
Chủ đề: giờ mở cửa, địa chỉ, chính sách, khuyến mãi, thẻ thành viên, wifi, parking, ship.
Ví dụ dễ: "Highlands mở cửa lúc mấy giờ?", "Có ship không?"
Ví dụ khó (hard): "Được đổi trả không nếu uống không ngon?", "App Highlands có tích điểm không?" """,

    "consultant": """Tạo {n} câu khách hàng cần TƯ VẤN chọn đồ uống tại Highlands Coffee.
Intent: "consultant"
Ngữ cảnh: thời tiết, sức khỏe, sở thích, ngân sách, dịp đặc biệt.
Ví dụ dễ: "Nên uống gì cho mát?", "Gợi ý đồ uống ít đường?"
Ví dụ khó (hard): "Có gì vừa ngon vừa rẻ không?", "Cái nào ít calo nhất?", "Uống cái gì tỉnh ngủ mà không đắng?" """,

    "ignore": """Tạo {n} câu KHÔNG LIÊN QUAN hoặc CÂU CẢM THÁN / TIẾNG ỒN.
Intent: "ignore"
Chủ đề: chào hỏi, cảm ơn, tạm biệt, cười, tiếng ồn, từ đệm.
Ví dụ: "Ừm...", "Hello", "haha", "hihi", "ồn quá", "abcxyz", "..." """ ,
}

# ─── Hard sample seeds (dùng trực tiếp + augment) ────────────────────────────
HARD_SAMPLES_SEED = {
    "order": [
        "Còn gì dưới 30k không?", "Cái nào ngon nhất?", "Menu hôm nay có gì mới?",
        "Cho tôi 1 cái bình thường thôi", "Đồ uống nào phổ biến nhất?",
        "Muốn uống cái gì đó lạ lạ", "Không biết chọn gì, bạn chọn giúp đi",
        "Có combo nào không?", "Size nào uống vừa vừa?",
    ],
    "faq": [
        "Được đổi trả không?", "Có tích điểm không?", "App có ưu đãi gì không?",
        "Mang thú cưng vào được không?", "Có chỗ ngồi ngoài trời không?",
        "Có nhận thanh toán QR không?", "Thẻ nào được giảm giá?",
    ],
    "consultant": [
        "Có gì vừa ngon vừa rẻ không?", "Cái nào ít calo nhất?",
        "Uống gì tỉnh ngủ mà không đắng?", "Đang ăn kiêng uống được gì?",
        "Đầu tuần buồn ngủ nên uống gì?", "Bạn bè 3 người khác gu thì gọi sao?",
        "Trời mưa uống gì ấm bụng?",
    ],
    "ignore": [
        "Ừm...", "Hello", "haha", "tiếng ồn", "hihi", "ok", "vậy hả",
        "đợi tí", "không có gì", "cảm ơn nhé", "bye", "chatbot ơi"
    ],
}


# ─── Checkpoint helpers ───────────────────────────────────────────────────────
def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        return json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
    return {intent: 0 for intent in INTENTS}


def save_checkpoint(progress: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")


def count_existing(intent: str) -> int:
    if not OUTPUT_FILE.exists():
        return 0
    count = 0
    for line in OUTPUT_FILE.read_text(encoding="utf-8").splitlines():
        try:
            if json.loads(line).get("intent") == intent:
                count += 1
        except Exception:
            pass
    return count


# ─── LLM API callers ──────────────────────────────────────────────────────────
def call_anthropic(api_key: str, prompt: str, n: int) -> list[dict]:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=4096,
        messages=[{"role": "user", "content": f"{SYSTEM_PROMPT}\n\n{prompt.format(n=n)}"}],
    )
    text = msg.content[0].text.strip()
    return _parse_json_response(text)


def call_openai(api_key: str, prompt: str, n: int) -> list[dict]:
    import openai
    client = openai.OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt.format(n=n)},
        ],
        max_tokens=4096,
        temperature=1.0,
    )
    text = resp.choices[0].message.content.strip()
    return _parse_json_response(text)


def _parse_json_response(text: str) -> list[dict]:
    """Parse JSON array from LLM response, handle code blocks."""
    # Strip markdown code blocks if present
    if "```" in text:
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        # Try to find JSON array in response
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except Exception:
                pass
    logger.warning(f"Failed to parse JSON response: {text[:200]}")
    return []


# ─── Demo mode (offline, no API) ─────────────────────────────────────────────
DEMO_TEMPLATES = {
    "order": [
        "Cho tôi {n} ly {drink} size {size}",
        "{drink} bao nhiêu tiền?",
        "Tôi muốn đặt {drink} {size}",
        "Menu có {drink} không?",
        "Thêm {drink} vào đơn giúp tôi",
    ],
    "faq": [
        "Highlands mở cửa lúc mấy giờ?",
        "Chi nhánh {location} ở đâu?",
        "Có ship về {location} không?",
        "Có wifi không?",
        "Chính sách đổi trả như thế nào?",
    ],
    "consultant": [
        "Nên uống gì cho mát?",
        "Gợi ý đồ uống cho buổi sáng?",
        "Uống gì ít đường?",
        "Có gì ngon không?",
        "Đang ăn kiêng uống được gì?",
    ],
    "ignore": [
        "Ừm...",
        "Hello",
        "haha",
        "hihi",
        "Cảm ơn nhé",
        "Tạm biệt",
        "...",
    ],
}

DRINKS = ["Phin Sữa Đá", "Bạc Xỉu", "Freeze Trà Xanh", "Trà Sen Vàng", "Phindi Choco"]
SIZES = ["S", "M", "L"]
LOCATIONS = ["quận 1", "quận 3", "Hà Nội", "Đà Nẵng"]


def generate_demo_samples(intent: str, n: int) -> list[dict]:
    templates = DEMO_TEMPLATES[intent]
    samples = []
    for i in range(n):
        tmpl = templates[i % len(templates)]
        text = tmpl.format(
            drink=random.choice(DRINKS),
            size=random.choice(SIZES),
            location=random.choice(LOCATIONS),
            n=random.randint(1, 3),
        )
        samples.append({"text": text, "intent": intent})
    # Add hard seeds
    hard = HARD_SAMPLES_SEED.get(intent, [])
    for seed in hard[:max(1, n // 5)]:
        samples.append({"text": seed, "intent": intent})
    return samples


# ─── Main pipeline ────────────────────────────────────────────────────────────
def generate_batch(api: str, api_key: str, intent: str, n: int) -> list[dict]:
    """Generate n samples for a given intent via LLM API."""
    prompt = INTENT_PROMPTS[intent]
    logger.info(f"Calling {api} API for intent='{intent}', n={n}...")
    try:
        if api == "anthropic":
            return call_anthropic(api_key, prompt, n)
        elif api == "openai":
            return call_openai(api_key, prompt, n)
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return []


def append_samples(samples: list[dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for s in samples:
            if "text" in s and "intent" in s:
                s["label"] = INTENT_LABELS.get(s["intent"], 3)
                f.write(json.dumps(s, ensure_ascii=False) + "\n")


def create_splits(test_ratio=0.1, val_ratio=0.1):
    """Split dataset into train/val/test."""
    if not OUTPUT_FILE.exists():
        logger.error("No data file found!")
        return

    all_data = []
    for line in OUTPUT_FILE.read_text(encoding="utf-8").splitlines():
        try:
            all_data.append(json.loads(line))
        except Exception:
            pass

    random.shuffle(all_data)
    n = len(all_data)
    n_test = int(n * test_ratio)
    n_val = int(n * val_ratio)

    test_data = all_data[:n_test]
    val_data = all_data[n_test:n_test + n_val]
    train_data = all_data[n_test + n_val:]

    def write_split(data, path):
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        logger.info(f"Saved {len(data)} samples → {path}")

    write_split(test_data, TEST_SPLIT_FILE)
    write_split(val_data, VAL_SPLIT_FILE)
    write_split(train_data, TRAIN_SPLIT_FILE)

    # Print distribution
    logger.info("\nDataset distribution:")
    for intent in INTENTS:
        total = sum(1 for d in all_data if d["intent"] == intent)
        logger.info(f"  {intent}: {total} samples")


def print_stats():
    """Print current generation stats."""
    if not OUTPUT_FILE.exists():
        logger.info("No data generated yet.")
        return
    counts = {i: 0 for i in INTENTS}
    total = 0
    for line in OUTPUT_FILE.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(line)
            if d.get("intent") in counts:
                counts[d["intent"]] += 1
                total += 1
        except Exception:
            pass
    logger.info(f"\nCurrent stats ({total}/{SAMPLES_PER_INTENT * len(INTENTS)} total):")
    for intent, count in counts.items():
        bar = "█" * (count // 20) + f" {count}/{SAMPLES_PER_INTENT}"
        logger.info(f"  {intent:12s}: {bar}")


def main():
    parser = argparse.ArgumentParser(description="Data Generation Pipeline - Module A1.2")
    parser.add_argument("--api", choices=["anthropic", "openai", "demo"], default="demo",
                        help="LLM API to use (demo=offline test mode)")
    parser.add_argument("--key", type=str, default="", help="API key")
    parser.add_argument("--batch-size", type=int, default=50, help="Samples per API call")
    parser.add_argument("--split", action="store_true", help="Only create train/val/test splits")
    parser.add_argument("--stats", action="store_true", help="Show current stats and exit")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.add(DATA_DIR / "generate.log", rotation="10 MB")

    if args.stats:
        print_stats()
        return

    if args.split:
        create_splits()
        return

    if args.api != "demo" and not args.key:
        logger.error(f"--key required for --api {args.api}")
        sys.exit(1)

    progress = load_checkpoint()
    logger.info(f"Starting data generation (mode={args.api})")
    logger.info(f"Checkpoint: {progress}")

    for intent in INTENTS:
        existing = count_existing(intent)
        remaining = SAMPLES_PER_INTENT - existing
        if remaining <= 0:
            logger.info(f"✅ '{intent}' complete ({existing} samples)")
            continue

        logger.info(f"Generating {remaining} samples for intent='{intent}'...")

        if args.api == "demo":
            samples = generate_demo_samples(intent, remaining)
            append_samples(samples)
            progress[intent] = existing + len(samples)
            save_checkpoint(progress)
            logger.info(f"  → {len(samples)} demo samples added")
        else:
            generated = 0
            while generated < remaining:
                batch_n = min(args.batch_size, remaining - generated)
                batch = generate_batch(args.api, args.key, intent, batch_n)
                if batch:
                    # Inject hard samples at ~22% rate
                    hard = HARD_SAMPLES_SEED.get(intent, [])
                    n_hard = max(1, int(len(batch) * HARD_SAMPLE_RATIO))
                    hard_batch = [{"text": s, "intent": intent}
                                  for s in random.sample(hard, min(n_hard, len(hard)))]
                    batch.extend(hard_batch)
                    append_samples(batch)
                    generated += len(batch)
                    progress[intent] = existing + generated
                    save_checkpoint(progress)
                    logger.info(f"  → {generated}/{remaining} done")
                else:
                    logger.warning("Empty batch, retrying in 5s...")
                    time.sleep(5)

        print_stats()

    # Auto-create splits after generation
    logger.info("\nCreating train/val/test splits...")
    create_splits()
    logger.info("\n✅ Data generation complete!")


if __name__ == "__main__":
    main()
