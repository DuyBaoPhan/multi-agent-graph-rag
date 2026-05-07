"""
Generator — Module B2.1
========================
Humanizes raw agent outputs using Qwen2.5-7B (via SGLang or API fallback).
Ensures the tone is consistent with Highlands Coffee brand.
"""

import httpx
import time
from loguru import logger
from src.config import get_settings

GENERATOR_SYSTEM_PROMPT = """Bạn là nhân viên Highlands Coffee vui vẻ, nhiệt tình.
Nhiệm vụ: Dựa trên dữ liệu thô từ hệ thống, hãy viết lại thành câu trả lời tự nhiên, thân thiện.
Quy tắc:
1. Không được tự bịa ra thông tin không có trong dữ liệu.
2. Dùng các từ ngữ lịch sự: 'Dạ', 'Anh/Chị', 'Highlands gửi mình ạ'.
3. Ngắn gọn, súc tích."""

class ResponseGenerator:
    def __init__(self):
        settings = get_settings()
        self.url = f"{settings.sglang_generator_host}/v1/chat/completions"
        self.is_healthy = False
        self._last_check = 0

    async def _check_health(self):
        """Check if SGLang Generator is alive once in a while."""
        now = time.time()
        if now - self._last_check < 60: # Check every 60s
            return self.is_healthy
        
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                resp = await client.get(self.url.replace("/v1/chat/completions", "/health"))
                self.is_healthy = resp.status_code == 200
        except:
            self.is_healthy = False
        
        self._last_check = now
        return self.is_healthy

    async def generate(self, raw_data: str, user_query: str) -> str:
        """Humanize response via LLM if available, otherwise use rule-base."""
        if await self._check_health():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(
                        self.url,
                        json={
                            "model": "generator",
                            "messages": [
                                {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
                                {"role": "user", "content": f"Dữ liệu: {raw_data}\nCâu hỏi khách: {user_query}"}
                            ],
                            "temperature": 0.7,
                        }
                    )
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.warning(f"SGLang Generator failed: {e}")
        
        # Fallback: Just return raw data if no LLM is configured for generation
        # In production, this would call GPT-4o or Qwen-7B
        return self._rule_based_polish(raw_data)

    async def _generate_via_sglang(self, data, query):
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.settings.sglang_generator_host}/v1/chat/completions",
                json={
                    "model": "generator",
                    "messages": [
                        {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Dữ liệu: {data}\nCâu hỏi khách: {query}"}
                    ],
                    "temperature": 0.7,
                }
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    def _rule_based_polish(self, data: str) -> str:
        """Simple fallback to add a polite touch without doubling markers."""
        res = data.strip()
        # Add 'Dạ' if not already present
        if not res.lower().startswith("dạ"):
            res = "Dạ, " + res
        # Add 'ạ' if not already present at the end
        if not res.endswith(("ạ", "!", ".", "?")):
            res += " ạ."
        return res

# Singleton
_generator = None

def get_generator() -> ResponseGenerator:
    global _generator
    if _generator is None:
        _generator = ResponseGenerator()
    return _generator
