"""
Router Serving — Module A1.1
==============================
Intent classification với 3 chế độ:
  1. SGLang  — dùng model AWQ đã fine-tune (production)
  2. API     — gọi Claude/GPT làm fallback (khi chưa có model)
  3. RuleBase — rule đơn giản (offline, zero-latency, dev mode)

Output chuẩn: {"action": "order" | "faq" | "consultant" | "chitchat"}
"""

import json
import os
import re
import time
from enum import Enum

import httpx
from loguru import logger
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ImportError:
    torch = None

from src.config import get_settings
from src.router.prompt_template import build_router_prompt

VALID_INTENTS = {"order", "faq", "consultant", "chitchat"}


class RouterMode(str, Enum):
    LOCAL_HF   = "local_hf"
    LOCAL_GGUF = "local_gguf"
    SGLANG     = "sglang"
    API        = "api"
    RULE_BASE  = "rule_base"


# ─── Rule-based fallback ──────────────────────────────────────────────────────
_ORDER_KEYWORDS = [
    r"\b(đặt|gọi|mua|order|thêm|bỏ|xóa|cho tôi|cho mình|lấy|bán|có|còn)\b",
    r"\b(menu|giá|bao nhiêu|tiền|size|s\b|m\b|l\b|ly|cốc|chai)\b",
    r"\b(phin|freeze|phindi|trà|cà phê|coffee|latte|cappuccino|bạc xỉu)\b",
]
_FAQ_KEYWORDS = [
    r"\b(giờ|mở cửa|đóng cửa|địa chỉ|ở đâu|chi nhánh|hotline|liên hệ)\b",
    r"\b(ship|giao hàng|delivery|wifi|parking|chỗ|đổi trả|hoàn tiền)\b",
    r"\b(khuyến mãi|voucher|coupon|thẻ thành viên|tích điểm|loyalty|app)\b",
    r"\b(chính sách|quy định|điều khoản)\b",
]
_CONSULTANT_KEYWORDS = [
    r"\b(nên|gợi ý|tư vấn|recommend|suggest|phù hợp|thích hợp)\b",
    r"\b(ngon|rẻ|ít đường|không đường|ít calo|diet|ăn kiêng|healthy)\b",
    r"\b(mát|lạnh|ấm|nóng|tươi mát|giải nhiệt)\b",
    r"\b(so sánh|khác nhau|cái nào|loại nào|món nào)\b",
]
_CHITCHAT_KEYWORDS = [
    r"\b(xin chào|chào|hello|hi\b|hey\b)\b",
    r"\b(cảm ơn|thank|tạm biệt|bye|goodbye|hẹn gặp)\b",
    r"\b(bạn tên|bạn là|ai vậy|bot|chatbot)\b",
]


def _rule_based_classify(text: str) -> str:
    """Fast rule-based classification with regex patterns."""
    text_lower = text.lower()

    scores = {intent: 0 for intent in VALID_INTENTS}
    for pattern in _CHITCHAT_KEYWORDS:
        if re.search(pattern, text_lower):
            scores["chitchat"] += 2
    for pattern in _FAQ_KEYWORDS:
        if re.search(pattern, text_lower):
            scores["faq"] += 2
    for pattern in _CONSULTANT_KEYWORDS:
        if re.search(pattern, text_lower):
            scores["consultant"] += 2
    for pattern in _ORDER_KEYWORDS:
        if re.search(pattern, text_lower):
            scores["order"] += 2

    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return "chitchat"  # default
    return best


# ─── SGLang caller ────────────────────────────────────────────────────────────
async def _classify_via_sglang(query: str) -> dict:
    settings = get_settings()
    messages = build_router_prompt(query)
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{settings.sglang_router_host}/v1/chat/completions",
            json={
                "model": "router",
                "messages": messages,
                "max_tokens": 20,
                "temperature": 0.0,
            },
        )
        resp.raise_for_status()
    return _parse_action(resp.json()["choices"][0]["message"]["content"])


# ─── API fallback caller ──────────────────────────────────────────────────────
async def _classify_via_api(query: str) -> dict:
    """Use Claude/GPT as fallback when fine-tuned model is not ready."""
    settings = get_settings()
    messages = build_router_prompt(query, use_few_shot=True)

    # Try Anthropic first, then OpenAI
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    if anthropic_key:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5",
                    "max_tokens": 20,
                    "system": messages[0]["content"],
                    "messages": messages[1:],
                },
            )
            resp.raise_for_status()
            text = resp.json()["content"][0]["text"]
            return _parse_action(text)

    if openai_key:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "max_tokens": 20,
                    "temperature": 0.0,
                },
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
            return _parse_action(text)

    raise RuntimeError("No API key configured (ANTHROPIC_API_KEY or OPENAI_API_KEY)")


# --- Local GGUF Engine ---
_llm_instance = None

def _get_local_llm():
    global _llm_instance
    if _llm_instance is None and Llama:
        model_path = "models/router/router_model.gguf"
        if os.path.exists(model_path):
            logger.info(f"Loading local GGUF router: {model_path}")
            _llm_instance = Llama(model_path=model_path, n_ctx=512, verbose=False)
        else:
            logger.warning(f"GGUF model not found at {model_path}")
    return _llm_instance

async def _classify_via_local_gguf(query: str) -> dict:
    llm = _get_local_llm()
    if not llm:
        raise RuntimeError("Local GGUF engine not initialized")
    
    prompt = f"<|im_start|>system\nPhân loại ý định: order, consultant, faq, ignore. Trả về JSON: {{\"action\": \"intent\"}}<|im_end|>\n<|im_start|>user\n{query}<|im_end|>\n<|im_start|>assistant\n"
    
    # Run inference (very fast for 1.5B model)
    output = llm(prompt, max_tokens=20, stop=["<|im_end|>"], echo=False)
    text = output["choices"][0]["text"].strip()
    return _parse_action(text)


# --- Local HF Engine (RTX 3060 Optimized) ---
_hf_model = None
_hf_tokenizer = None

def _get_local_hf():
    global _hf_model, _hf_tokenizer
    if _hf_model is None and torch:
        # Tự động kiểm tra các đường dẫn có thể có
        paths_to_check = ["models/router", "models/router/router_merged", "router_merged"]
        model_path = None
        for p in paths_to_check:
            if os.path.exists(os.path.join(p, "config.json")):
                model_path = p
                break
        
        if model_path:
            logger.info(f"Loading local HF router from {model_path} to CPU (Optimized)...")
            _hf_tokenizer = AutoTokenizer.from_pretrained(model_path)
            _hf_model = AutoModelForCausalLM.from_pretrained(
                model_path,
                low_cpu_mem_usage=True
            )
        else:
            logger.warning("HF model not found in any of: models/router, models/router/router_merged, or router_merged")
    return _hf_model, _hf_tokenizer

async def _classify_via_local_hf(query: str) -> dict:
    model, tokenizer = _get_local_hf()
    if not model:
        raise RuntimeError("Local HF engine not initialized")
    
    prompt = f"<|im_start|>system\nPhân loại ý định: order, consultant, faq, chitchat. Trả về JSON: {{\"action\": \"intent\"}}<|im_end|>\n<|im_start|>user\n{query}<|im_end|>\n<|im_start|>assistant\n"
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=20, do_sample=False)
    
    text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return _parse_action(text)


# ─── JSON parser with fallback ────────────────────────────────────────────────
def _parse_action(text: str) -> dict:
    """Parse JSON {"action": "..."} from model output with fallback."""
    text = text.strip()
    try:
        data = json.loads(text)
        action = data.get("action", "chitchat")
        if action in VALID_INTENTS:
            return {"action": action}
    except json.JSONDecodeError:
        pass

    # Fallback: search for intent keyword in text
    for intent in VALID_INTENTS:
        if intent in text.lower():
            logger.warning(f"Router: JSON parse failed, extracted '{intent}' from text")
            return {"action": intent}

    logger.warning(f"Router: cannot parse response '{text}', defaulting to chitchat")
    return {"action": "chitchat"}


# ─── Main classify function ───────────────────────────────────────────────────
async def classify_intent(
    query: str,
    mode: RouterMode | None = None,
) -> dict:
    """
    Classify user query into one of 4 intents.

    Auto-selects mode:
      - SGLANG if SGLang server is healthy
      - API if API key available
      - RULE_BASE as final fallback

    Returns: {"action": "order" | "faq" | "consultant" | "chitchat",
              "mode": "sglang|api|rule_base", "latency_ms": float}
    """
    t0 = time.perf_counter()
    settings = get_settings()

    # Auto-detect mode if not specified
    if mode is None:
        mode = await _detect_best_mode(settings.sglang_router_host)

    result: dict = {"action": "chitchat"}
    try:
        if mode == RouterMode.LOCAL_HF:
            result = await _classify_via_local_hf(query)
        elif mode == RouterMode.LOCAL_GGUF:
            result = await _classify_via_local_gguf(query)
        elif mode == RouterMode.SGLANG:
            result = await _classify_via_sglang(query)
        elif mode == RouterMode.API:
            result = await _classify_via_api(query)
        else:
            result = {"action": _rule_based_classify(query)}
    except Exception as e:
        logger.warning(f"Router mode={mode} failed: {e}. Falling back to rule_base.")
        result = {"action": _rule_based_classify(query)}
        mode = RouterMode.RULE_BASE

    latency_ms = (time.perf_counter() - t0) * 1000
    result["mode"] = mode
    result["latency_ms"] = round(latency_ms, 1)

    logger.info(
        f"Router: '{query[:40]}' → {result['action']} "
        f"[{mode}, {latency_ms:.0f}ms]"
    )
    return result


async def _detect_best_mode(sglang_url: str) -> RouterMode:
    """Check which router mode is available."""
    # Priority 1: Local Fine-tuned Merged Model (HF Format)
    paths_to_check = ["models/router", "models/router/router_merged", "router_merged"]
    for p in paths_to_check:
        if os.path.exists(os.path.join(p, "config.json")):
            return RouterMode.LOCAL_HF

    # Priority 2: Local GGUF (For CPU/Edge)
    if os.path.exists("models/router/router_model.gguf"):
        return RouterMode.LOCAL_GGUF

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{sglang_url}/health")
            if resp.status_code == 200:
                return RouterMode.SGLANG
    except Exception:
        pass

    if os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"):
        return RouterMode.API

    return RouterMode.RULE_BASE
