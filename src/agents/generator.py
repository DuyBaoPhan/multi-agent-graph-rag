"""
Generator — Module B2.1
========================
Humanizes raw agent outputs using Qwen2.5-7B (via SGLang or API fallback).
Ensures the tone is consistent with Highlands Coffee brand.
"""

import os
import httpx
import time
from loguru import logger
from src.config import get_settings

GENERATOR_SYSTEM_PROMPT = """Bạn là nhân viên Highlands Coffee vui vẻ, nhiệt tình.
Nhiệm vụ: Dựa trên dữ liệu thô từ hệ thống, hãy viết lại thành câu trả lời tự nhiên, thân thiện.
Quy tắc:
1. TUYỆT ĐỐI KHÔNG tự bịa ra thông tin không có trong dữ liệu thô.
2. TUYỆT ĐỐI KHÔNG TỰ LÀM TOÁN. Số tiền 'Tổng bill' trong dữ liệu thô là kết quả CUỐI CÙNG đã được hệ thống tính toán chính xác. Bạn PHẢI GIỮ NGUYÊN con số đó, không được cộng thêm hay bớt đi bất kỳ đơn vị nào.
3. QUAN TRỌNG: Hãy xem CÂU HỎI MỚI NHẤT của khách. Nếu câu mới nhất là tiếng Anh, bạn PHẢI trả lời hoàn toàn bằng tiếng Anh. Nếu là tiếng Việt thì trả lời tiếng Việt.
4. Nếu khách dùng tiếng Việt, hãy dùng các từ ngữ lịch sự: 'Dạ', 'Anh/Chị'.
5. Giữ câu trả lời ngắn gọn, tập trung vào đúng câu hỏi của khách. Không lặp lại các món cũ trong lịch sử nếu không cần thiết."""

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

    async def generate(self, raw_data: str, user_query: str, history: list[dict] = None) -> str:
        """Humanize response via LLM if available, otherwise use rule-base."""
        if await self._check_health():
            try:
                messages = [{"role": "system", "content": GENERATOR_SYSTEM_PROMPT}]
                # No history for generator to prevent cross-turn math hallucinations
                pass
                
                messages.append({"role": "user", "content": f"Dữ liệu thô từ hệ thống: {raw_data}\nCâu hỏi hiện tại của khách: {user_query}"})

                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(
                        self.url,
                        json={
                            "model": "generator",
                            "messages": messages,
                            "temperature": 0.1, # Min temp for max precision
                        }
                    )
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.warning(f"SGLang Generator failed: {e}")
                
        # API Fallback if SGLang is down
        # Detect language of current query
        q_lower = user_query.lower()
        is_english = any(w in q_lower for w in ["hello", "hi", "hey", "thank", "bye", "what", "how", "menu", "order"]) and not any(w in q_lower for w in ["chào", "cảm ơn", "bạn", "tôi", "cho", "ly", "thêm", "đặt"])
        
        lang_instruction = "PHẢI trả lời hoàn toàn bằng TIẾNG ANH (ENGLISH)." if is_english else "PHẢI trả lời hoàn toàn bằng TIẾNG VIỆT. Dùng các từ 'Dạ', 'Anh/Chị'."
        
        api_messages = [{"role": "system", "content": GENERATOR_SYSTEM_PROMPT + f"\n\nLỆNH BẮT BUỘC CHO LƯỢT NÀY: {lang_instruction}"}]
        # No history for generator to prevent cross-turn math hallucinations
        pass
        api_messages.append({"role": "user", "content": f"Dữ liệu thô từ hệ thống: {raw_data}\nCâu hỏi hiện tại của khách: {user_query}"})

        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        lm_studio_host = os.getenv("LM_STUDIO_HOST", "http://127.0.0.1:1234")

        # 1. Try LM Studio first (Local, Free)
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                lm_health = await client.get(f"{lm_studio_host}/v1/models")
            if lm_health.status_code == 200:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{lm_studio_host}/v1/chat/completions",
                        json={
                            "model": "local-model",
                            "messages": api_messages,
                            "max_tokens": 150,
                            "temperature": 0.1,
                        },
                    )
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            pass # LM Studio not running

        # 2. Try Anthropic
        if anthropic_key:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": anthropic_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json",
                        },
                        json={
                            "model": "claude-3-haiku-20240307",
                            "max_tokens": 200,
                            "system": api_messages[0]["content"],
                            "messages": api_messages[1:],
                        },
                    )
                    resp.raise_for_status()
                    return resp.json()["content"][0]["text"]
            except Exception as e:
                logger.warning(f"Anthropic API fallback failed: {e}")

        # 3. Try OpenAI
        if openai_key:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {openai_key}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": api_messages,
                            "max_tokens": 200,
                            "temperature": 0.4,
                        },
                    )
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.warning(f"OpenAI API fallback failed: {e}")
        
        # Final Fallback: Rule-based
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
        # Skip Vietnamese polite words if it's English
        if any(w in res.lower() for w in ["hello", "thank", "bye", "you're", "i'm", "how can"]):
            return res
            
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
