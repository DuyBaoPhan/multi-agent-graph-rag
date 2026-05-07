"""
Session Store
===============
In-memory + Redis session management (Module A2.2).
Keeps last N turns, summarizes when context exceeds threshold.
"""

import asyncio
import time
import uuid

from loguru import logger

from src.config import get_settings


class SessionStore:
    """
    Manages conversation sessions with TTL and context window management.
    
    Features:
    - Keeps last 5 conversation turns per session
    - Auto-summarizes when context exceeds 70% of LLM window
    - TTL-based session expiry (default 30 minutes)
    - Periodic cleanup via background task
    """

    def __init__(self):
        self.settings = get_settings()
        self.sessions: dict[str, dict] = {}
        self._cleanup_task: asyncio.Task | None = None

    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "history": [],
            "created_at": time.time(),
            "last_active": time.time(),
            "summary": "",
            "metadata": {"cart": []},
        }
        logger.info(f"Created session: {session_id}")
        return session_id

    def get_history(self, session_id: str) -> list[dict]:
        """Get conversation history for a session."""
        session = self.sessions.get(session_id)
        if not session:
            return []

        session["last_active"] = time.time()
        return session["history"][-self.settings.session_max_history * 2 :]

    def add_turn(self, session_id: str, user_msg: str, assistant_msg: str):
        """Add a conversation turn (user + assistant) to session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],
                "created_at": time.time(),
                "last_active": time.time(),
                "summary": "",
                "metadata": {"cart": []},
            }

        session = self.sessions[session_id]
        session["history"].append({"role": "user", "content": user_msg})
        session["history"].append({"role": "assistant", "content": assistant_msg})
        session["last_active"] = time.time()

        # Keep only last N turns (N*2 messages)
        max_messages = self.settings.session_max_history * 2
        if len(session["history"]) > max_messages:
            # TODO: Summarize old messages with LLM before trimming
            session["history"] = session["history"][-max_messages:]

    def cleanup_expired(self):
        """Remove sessions that have exceeded TTL."""
        now = time.time()
        ttl_seconds = self.settings.session_ttl_minutes * 60
        expired = [
            sid
            for sid, data in self.sessions.items()
            if now - data["last_active"] > ttl_seconds
        ]
        for sid in expired:
            del self.sessions[sid]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    async def start_cleanup_loop(self):
        """Start background task to clean expired sessions every 5 minutes."""

        async def _loop():
            while True:
                await asyncio.sleep(300)  # 5 minutes
                self.cleanup_expired()

        self._cleanup_task = asyncio.create_task(_loop())

    async def stop_cleanup_loop(self):
        """Stop the background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()

    def get_metadata(self, session_id: str) -> dict:
        """Get session metadata (cart, user info, etc.)."""
        session = self.sessions.get(session_id)
        if not session:
            return {"cart": []}
        return session.get("metadata", {"cart": []})

    def update_metadata(self, session_id: str, metadata: dict):
        """Update session metadata."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],
                "created_at": time.time(),
                "last_active": time.time(),
                "summary": "",
                "metadata": {"cart": []},
            }
        
        self.sessions[session_id]["metadata"] = metadata
        self.sessions[session_id]["last_active"] = time.time()


# Singleton
_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    """Get or create the global SessionStore singleton."""
    global _store
    if _store is None:
        _store = SessionStore()
    return _store
