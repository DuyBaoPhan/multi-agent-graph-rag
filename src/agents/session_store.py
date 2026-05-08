"""
Session Store
===============
Hardened Redis Session Management.
Ensures context is isolated per session_id and persisted in Redis.
"""

import json
import time
import uuid
import asyncio
from loguru import logger

from src.config import get_settings
from src.llm_serving.cache.redis_cache import get_redis_cache

class SessionStore:
    def __init__(self):
        self.settings = get_settings()
        self.redis = get_redis_cache()
        self._local_sessions: dict[str, dict] = {}

    async def _get_session(self, session_id: str) -> dict:
        """Force retrieval from Redis or Local with strict isolation."""
        if not session_id:
            return {"history": [], "summary": "", "metadata": {"cart": []}, "last_active": time.time()}

        if self.redis:
            try:
                data = await self.redis.get(f"session:{session_id}")
                if data: 
                    # Ensure metadata and cart exist
                    if "metadata" not in data: data["metadata"] = {"cart": []}
                    return data
            except Exception as e:
                logger.warning(f"Redis session get failed for {session_id}: {e}")
        
        # Fallback to local
        if session_id not in self._local_sessions:
            self._local_sessions[session_id] = {
                "history": [],
                "summary": "",
                "metadata": {"cart": []},
                "last_active": time.time()
            }
        return self._local_sessions[session_id]

    async def _save_session(self, session_id: str, data: dict):
        """Strict save to Redis with TTL."""
        if not session_id: return
        data["last_active"] = time.time()
        
        if self.redis:
            try:
                await self.redis.set(f"session:{session_id}", data, ttl=1800)
            except Exception as e:
                logger.warning(f"Redis session save failed for {session_id}: {e}")
        
        # Always update local for fast access/fallback
        self._local_sessions[session_id] = data

    async def get_history(self, session_id: str) -> list[dict]:
        session = await self._get_session(session_id)
        return session.get("history", [])

    async def add_turn(self, session_id: str, user_msg: str, assistant_msg: str):
        session = await self._get_session(session_id)
        session["history"].append({"role": "user", "content": user_msg})
        session["history"].append({"role": "assistant", "content": assistant_msg})
        
        # Sliding window
        max_msgs = self.settings.session_max_history * 2
        if len(session["history"]) > max_msgs:
            session["history"] = session["history"][-max_msgs:]
        
        await self._save_session(session_id, session)

    async def get_metadata_async(self, session_id: str) -> dict:
        session = await self._get_session(session_id)
        return session.get("metadata", {"cart": []})

    async def update_metadata(self, session_id: str, metadata: dict):
        session = await self._get_session(session_id)
        session["metadata"] = metadata
        await self._save_session(session_id, session)

# Singleton
_store = None

def get_session_store() -> SessionStore:
    global _store
    if _store is None:
        _store = SessionStore()
    return _store
