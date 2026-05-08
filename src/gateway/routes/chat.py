"""
Chat Route — Gateway Layer
==========================
Synchronized with Frontend (demo/index.html)
"""

import uuid
import time
from fastapi import APIRouter, Request, HTTPException
from loguru import logger
from pydantic import BaseModel

from src.router.serving import classify_intent
from src.agents.dispatcher import AgentDispatcher
from src.agents.session_store import get_session_store
from src.agents.generator import get_generator
from src.llm_serving.cache.semantic_cache import get_semantic_cache
from src.guardrails.fallback import get_fallback_response

router = APIRouter()
_dispatcher = AgentDispatcher()
_session_store = get_session_store()

class ChatRequest(BaseModel):
    message: str # Match frontend: body.message
    session_id: str | None = None

class ChatResponse(BaseModel):
    reply: str # Match frontend: data.reply
    intent: str
    agent: str
    latency_ms: float
    session_id: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.time()
    sanitized = request.message.strip() # Using .message
    session_id = request.session_id or str(uuid.uuid4())
    
    if not sanitized:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # 0. Identify Intent
    try:
        router_result = await classify_intent(sanitized)
        intent = router_result["action"]
        router_mode = str(router_result.get("mode", "unknown"))
    except Exception as e:
        logger.error(f"Router failed: {e}")
        intent, router_mode = "ignore", "fallback"

    # 1. Semantic Cache Check
    sem_cache = get_semantic_cache()
    cached_reply = await sem_cache.get(sanitized, intent=intent)
    if cached_reply:
        return ChatResponse(
            reply=cached_reply, # Using reply
            intent="cached",
            agent="semantic_cache",
            latency_ms=0,
            session_id=session_id
        )

    # 2. Dispatch
    history = await _session_store.get_history(session_id)
    try:
        raw_reply = await _dispatcher.dispatch(intent, sanitized, history, session_id)
        
        # 3. Humanize
        generator = get_generator()
        final_reply = await generator.generate(raw_reply, sanitized, history)
        
        # 4. Save to Cache
        await sem_cache.set(sanitized, final_reply, intent=intent)
        
        # 5. Save to Session (Redis)
        await _session_store.add_turn(session_id, sanitized, final_reply)
        
        latency = (time.time() - start_time) * 1000
        return ChatResponse(
            reply=final_reply, # Using reply
            intent=intent,
            agent=f"{intent}_agent ({router_mode})",
            latency_ms=round(latency, 2),
            session_id=session_id
        )

    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        fallback_msg = get_fallback_response(intent)
        return ChatResponse(
            reply=fallback_msg, # Using reply
            intent=intent,
            agent="fallback_guardrail",
            latency_ms=0,
            session_id=session_id
        )
