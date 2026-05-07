"""
Chat Routes
=============
Main chat endpoint with SSE streaming (Module B2.2).
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request payload."""
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Chat response payload (non-streaming)."""
    reply: str
    session_id: str
    intent: str
    agent: str
    cached: bool = False


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    
    Pipeline:
    1. Router classifies intent
    2. Dispatcher selects agent
    3. Agent processes query (with RAG if needed)
    4. Response returned (with session tracking)
    """
    # TODO: Implement full pipeline
    return ChatResponse(
        reply="Xin chào! Tôi là trợ lý Highlands Coffee. Hệ thống đang được phát triển.",
        session_id=request.session_id or "new-session",
        intent="chitchat",
        agent="default",
        cached=False,
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    SSE streaming chat endpoint.
    
    Returns Server-Sent Events with token-by-token generation.
    """
    # TODO: Implement SSE streaming with sse-starlette
    pass
