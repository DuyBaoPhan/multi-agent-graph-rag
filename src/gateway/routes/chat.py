"""
Chat Routes — Module A1, A2, B2.2
====================================
Chat endpoint + SSE streaming endpoint.
"""

import asyncio
import json
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from loguru import logger
from sse_starlette.sse import EventSourceResponse

from src.router.serving import classify_intent
from src.agents.dispatcher import AgentDispatcher
from src.agents.session_store import SessionStore
from src.guardrails.input_validator import validate_input
from src.guardrails.fallback import get_fallback_response
from src.agents.generator import get_generator
from src.llm_serving.cache.semantic_cache import get_semantic_cache

router = APIRouter()

_dispatcher = AgentDispatcher()
_session_store = SessionStore()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    intent: str
    agent: str
    router_mode: str = "unknown"
    latency_ms: float = 0.0
    cached: bool = False


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint — full pipeline."""
    is_valid, sanitized = validate_input(request.message)
    if not is_valid:
        raise HTTPException(status_code=400, detail=sanitized)

    session_id = request.session_id or str(uuid.uuid4())
    history = _session_store.get_history(session_id)

    try:
        router_result = await classify_intent(sanitized)
        intent = router_result["action"]
        router_mode = str(router_result.get("mode", "unknown"))
        latency_ms = router_result.get("latency_ms", 0.0)
    except Exception as e:
        logger.error(f"Router failed: {e}")
        intent, router_mode, latency_ms = "chitchat", "fallback", 0.0

    try:
        reply = await _dispatcher.dispatch(intent, sanitized, history, session_id)
        # Humanize response via Qwen-7B Generator (Module B2.1)
        generator = get_generator()
        reply = await generator.generate(reply, sanitized)
        
        # 3. Store in Semantic Cache
        await cache.set(sanitized, reply)
    except Exception as e:
        logger.error(f"Agent failed: {e}")
        reply = get_fallback_response(intent)

    _session_store.add_turn(session_id, sanitized, reply)

    return ChatResponse(
        reply=reply,
        session_id=session_id,
        intent=intent,
        agent=f"{intent}_agent",
        router_mode=router_mode,
        latency_ms=latency_ms,
        cached=False,
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE streaming endpoint — sends response token by token (Module B2.2)."""
    is_valid, sanitized = validate_input(request.message)
    if not is_valid:
        raise HTTPException(status_code=400, detail=sanitized)

    session_id = request.session_id or str(uuid.uuid4())
    history = _session_store.get_history(session_id)

    try:
        router_result = await classify_intent(sanitized)
        intent = router_result["action"]
    except Exception:
        intent = "chitchat"

    try:
        full_reply = await _dispatcher.dispatch(intent, sanitized, history, session_id)
    except Exception:
        full_reply = get_fallback_response(intent)

    _session_store.add_turn(session_id, sanitized, full_reply)

    async def event_generator():
        """Simulate token-by-token streaming from pre-generated response."""
        # Send metadata first
        yield {
            "event": "metadata",
            "data": json.dumps({
                "session_id": session_id,
                "intent": intent,
                "agent": f"{intent}_agent",
            }, ensure_ascii=False),
        }

        # Stream tokens (split by words for simulation)
        words = full_reply.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield {"data": json.dumps({"token": token}, ensure_ascii=False)}
            await asyncio.sleep(0.03)  # ~30ms per token

        # Done signal — NOT json.parse'd
        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())
